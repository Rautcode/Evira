import os
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional
from app.utils.config_manager import ConfigManager

router = APIRouter(tags=["system-settings"], prefix="/system-settings")

class SystemSettingsData(BaseModel):
    opcua_url: Optional[str] = None
    opcua_username: Optional[str] = None
    opcua_password: Optional[str] = None
    mssql_server: Optional[str] = None
    mssql_database: Optional[str] = None
    mssql_auth_type: Optional[str] = None
    mssql_username: Optional[str] = None
    mssql_password: Optional[str] = None

@router.get("/")
def get_system_settings():
    """Retrieve the active system configuration overrides."""
    config = ConfigManager.load_config()
    
    return {
        "opcua_url": config.get("opcua_url", os.getenv("OPC_UA_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")),
        "opcua_username": config.get("opcua_username", os.getenv("OPC_UA_USERNAME", "")),
        "opcua_password": "", # Never return passwords
        "mssql_server": config.get("mssql_server", os.getenv("MSSQL_SERVER", "localhost")),
        "mssql_database": config.get("mssql_database", os.getenv("MSSQL_DATABASE", "scada_reports")),
        "mssql_auth_type": config.get("mssql_auth_type", os.getenv("MSSQL_AUTH_TYPE", "windows")),
        "mssql_username": config.get("mssql_username", os.getenv("MSSQL_USERNAME", "")),
        "mssql_password": "" # Never return passwords
    }

@router.put("/")
async def update_system_settings(data: SystemSettingsData = Body(...)):
    """Save new system settings and trigger hot-reloads."""
    new_config = {}
    
    # Only update provided fields (passwords might be empty if unchanged)
    if data.opcua_url is not None: new_config["opcua_url"] = data.opcua_url
    if data.opcua_username is not None: new_config["opcua_username"] = data.opcua_username
    if data.opcua_password: new_config["opcua_password"] = data.opcua_password
    
    if data.mssql_server is not None: new_config["mssql_server"] = data.mssql_server
    if data.mssql_database is not None: new_config["mssql_database"] = data.mssql_database
    if data.mssql_auth_type is not None: new_config["mssql_auth_type"] = data.mssql_auth_type
    if data.mssql_username is not None: new_config["mssql_username"] = data.mssql_username
    if data.mssql_password: new_config["mssql_password"] = data.mssql_password
    
    # Merge into existing config so saving (e.g.) OPC settings does not wipe the
    # SQL settings or the onboarding flag.
    ConfigManager.update_config(new_config)

    # Trigger WinCC Hot Reload if OPC UA settings were changed
    if any(k.startswith("opcua_") for k in new_config.keys()):
        from app.services.wincc_service import wincc_monitor
        await wincc_monitor.reconnect()

    # Database connections will automatically pick up the new config
    # on their next DBConnector initialization

    return {"success": True, "message": "System settings updated and services restarted successfully."}


@router.post("/test")
async def test_connection(data: SystemSettingsData = Body(...)):
    """Validate OPC UA and SQL credentials WITHOUT saving them."""
    result = {"opcua_ok": False, "opcua_error": None, "mssql_ok": False, "mssql_error": None}

    # --- SQL Server ---
    if data.mssql_server:
        from app.services.auth_service import validate_sql_login
        r = validate_sql_login(
            server=data.mssql_server,
            database=data.mssql_database or "master",
            username=data.mssql_username,
            password=data.mssql_password or "",
            auth_type=(data.mssql_auth_type or "sql"),
            enforce_allowlist=False,  # admin is configuring a new server here
        )
        result["mssql_ok"] = bool(r.get("success"))
        if not r.get("success"):
            result["mssql_error"] = r.get("error")
    else:
        result["mssql_error"] = "No SQL server provided"

    # --- OPC UA ---
    if data.opcua_url:
        try:
            from asyncua import Client
            client = Client(data.opcua_url, timeout=5)
            if data.opcua_username and data.opcua_password:
                client.set_user(data.opcua_username)
                client.set_password(data.opcua_password)
            await client.connect()
            await client.disconnect()
            result["opcua_ok"] = True
        except Exception as e:
            result["opcua_error"] = str(e)[:200]
    else:
        result["opcua_error"] = "No OPC UA URL provided"

    return result
