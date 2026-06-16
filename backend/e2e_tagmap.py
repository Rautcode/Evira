"""Verify configurable tag mapping: migration, seed, matching, and CRUD API."""
import os

SERVER = os.getenv("MSSQL_SERVER", "localhost,14333")
os.environ["MSSQL_SERVER"] = SERVER
os.environ.setdefault("JWT_SECRET", "e2e-tagmap-secret")
os.environ.setdefault("MSSQL_DATABASE", "scada_reports")
os.environ.setdefault("MSSQL_AUTH_TYPE", "sql")
os.environ.setdefault("MSSQL_USERNAME", "sa")
os.environ.setdefault("MSSQL_PASSWORD", "Scada!Pass2026")
os.environ["MSSQL_ALLOWED_SERVERS"] = SERVER

from app.utils.migrations import run_migrations
from app.services.tag_mapping_service import tag_mapping_service
from fastapi.testclient import TestClient
from app.main import app

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

# 1. Apply migrations (creates + seeds tag_mapping_rules)
run_migrations()
tag_mapping_service.invalidate()
rules = tag_mapping_service.get_rules()
check("seeded machine rules", len(rules["machine"]) >= 10, f"count={len(rules['machine'])}")
check("seeded parameter rules", len(rules["parameter"]) >= 10, f"count={len(rules['parameter'])}")

# 2. Default heuristics still match (unchanged behavior)
check("extruder->M001", tag_mapping_service.match_machine("Extruder_01 Line A") == "M001")
check("temp->Temperature", (tag_mapping_service.match_parameter("Zone1_Temp") or {}).get("parameter") == "Temperature")
check("unknown tag -> no match", tag_mapping_service.match_machine("RX-9000-foo") is None)

# 3. CRUD API: add a real-world custom rule and confirm it matches after reload
with TestClient(app) as client:
    r = client.post("/auth/login", json={
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
    })
    h = {"Authorization": f"Bearer {r.json()['token']}"}

    r = client.get("/tag-mapping/", headers=h)
    check("API list rules", r.status_code == 200 and len(r.json()) >= 20, f"status={r.status_code} n={len(r.json()) if r.status_code==200 else '-'}")

    # Real factory tag e.g. "RX100" should map to M001 once we add a rule
    r = client.post("/tag-mapping/", headers=h, json={
        "rule_type": "machine", "match_text": "rx100", "machine_id": "M001", "priority": 5
    })
    check("API create rule", r.status_code == 200, f"status={r.status_code}")
    rule_id = r.json().get("id")

    check("custom rule matches after invalidate",
          tag_mapping_service.match_machine("RX100_Pump_Temp") == "M001")

    # validation: bad rule_type rejected
    r = client.post("/tag-mapping/", headers=h, json={"rule_type": "bogus", "match_text": "x"})
    check("API rejects bad rule_type", r.status_code == 400, f"status={r.status_code}")

    # cleanup
    r = client.delete(f"/tag-mapping/{rule_id}", headers=h)
    check("API delete rule", r.status_code == 200, f"status={r.status_code}")

passed = sum(results)
print(f"\n==== {passed}/{len(results)} tag-mapping checks passed ====")
raise SystemExit(0 if passed == len(results) else 1)
