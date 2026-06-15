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
    
    ConfigManager.save_config(new_config)
    
    # Trigger WinCC Hot Reload if OPC UA settings were changed
    if any(k.startswith("opcua_") for k in new_config.keys()):
        from app.services.wincc_service import wincc_monitor
        await wincc_monitor.reconnect()
        
    # Database connections will automatically pick up the new config 
    # on their next DBConnector initialization
        
    return {"success": True, "message": "System settings updated and services restarted successfully."}
