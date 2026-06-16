"""Onboarding/setup status for the guided 5-step wizard."""

import logging

from fastapi import APIRouter

from app.utils.config_manager import ConfigManager
from app.utils.db import get_connection_status

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"], prefix="/setup")


@router.get("/status")
def get_setup_status():
    """Per-step onboarding readiness + an overall completed flag for the wizard."""
    config = ConfigManager.load_config()

    # Connect: credentials configured
    connect_ok = bool(config.get("opcua_url")) and bool(config.get("mssql_server"))

    # Discover: tags found on the OPC UA server
    total_tags = 0
    wincc_connected = False
    try:
        from app.services.wincc_service import wincc_monitor
        status = wincc_monitor.get_status()
        total_tags = int(status.get("total_tags", 0))
        wincc_connected = bool(status.get("connected", False))
    except Exception as e:
        logger.debug(f"wincc status unavailable: {e}")

    # Map: at least one mapping rule
    rules_count = 0
    try:
        from app.services.tag_mapping_service import tag_mapping_service
        rules_count = len(tag_mapping_service.list_rules())
    except Exception as e:
        logger.debug(f"tag mapping rules unavailable: {e}")

    # Preview: templates available
    templates_count = 0
    try:
        from app.services.template_service import TemplateService
        templates_count = len(TemplateService().list_templates())
    except Exception as e:
        logger.debug(f"templates unavailable: {e}")

    # Automate: scheduled jobs
    jobs_count = 0
    try:
        from app.routers.scheduler import scheduler
        jobs_count = len(scheduler.get_jobs())
    except Exception as e:
        logger.debug(f"scheduler unavailable: {e}")

    completed = bool(config.get("onboarding_complete")) or (connect_ok and total_tags > 0)

    return {
        "completed": completed,
        "database_reachable": get_connection_status("database"),
        "steps": {
            "connect": {"done": connect_ok, "wincc_connected": wincc_connected},
            "discover": {"done": total_tags > 0, "tag_count": total_tags},
            "map": {"done": rules_count > 0, "rule_count": rules_count},
            "preview": {"done": templates_count > 0, "template_count": templates_count},
            "automate": {"done": jobs_count > 0, "job_count": jobs_count},
        },
    }


@router.post("/complete")
def complete_setup():
    """Mark onboarding as finished (merge-safe), so users aren't redirected again."""
    ConfigManager.update_config({"onboarding_complete": True})
    return {"success": True, "message": "Setup complete"}
