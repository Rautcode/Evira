"""WinCC-style OPC UA server simulator.

Exposes realistic machine tags (names carry machine + parameter keywords so the
app's auto-discovery + mapping rules classify them) and updates their values
every couple of seconds to simulate live factory telemetry. Used to prove the
full live path: connect -> auto-discover -> subscribe -> persist -> report.

Run standalone:  python opcua_simulator.py
"""
import asyncio
import logging
import random

from asyncua import Server, ua

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("opcua-sim")

ENDPOINT = "opc.tcp://0.0.0.0:4840/freeopcua/server/"

# (display name, min, max). Names include a machine keyword (extruder/molding/
# chiller/packaging/mixer) and a parameter keyword (temp/pressure/speed/force/
# flow/count/error) so the default mapping rules pick them up.
TAGS = [
    ("Extruder_Alpha_Temperature", 180, 220),
    ("Extruder_Alpha_Pressure", 80, 120),
    ("Extruder_Alpha_Speed", 50, 75),
    ("Molding_Beta_Pressure", 90, 130),
    ("Molding_Beta_Force", 500, 600),
    ("Chiller_Gamma_FlowRate", 100, 150),
    ("Chiller_Gamma_Temperature", 5, 12),
    ("Packaging_Delta_PackCount", 10, 30),
    ("Packaging_Delta_ErrorRate", 0, 2),
    ("Mixer_Epsilon_Speed", 100, 200),
]


async def main():
    server = Server()
    await server.init()
    server.set_endpoint(ENDPOINT)
    server.set_server_name("WinCC OPC UA Simulator")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    idx = await server.register_namespace("http://winccsim.factory")
    plant = await server.nodes.objects.add_folder(idx, "Factory")

    nodes = []
    for name, lo, hi in TAGS:
        var = await plant.add_variable(idx, name, float(round((lo + hi) / 2, 2)))
        await var.set_writable()
        nodes.append((var, lo, hi))

    logger.info("WinCC OPC UA simulator serving %d tags on %s", len(nodes), ENDPOINT)
    async with server:
        while True:
            for var, lo, hi in nodes:
                await var.write_value(round(random.uniform(lo, hi), 2))
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
