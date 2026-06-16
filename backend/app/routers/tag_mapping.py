"""CRUD API for configurable OPC UA tag -> machine/parameter mapping rules."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

from app.services.tag_mapping_service import tag_mapping_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tag-mapping"], prefix="/tag-mapping")


class TagRule(BaseModel):
    rule_type: str  # 'machine' | 'parameter'
    match_text: str
    machine_id: Optional[str] = None
    parameter: Optional[str] = None
    unit: Optional[str] = None
    priority: int = 100
    active: bool = True


def _validate(rule: TagRule) -> None:
    if rule.rule_type not in ("machine", "parameter"):
        raise HTTPException(status_code=400, detail="rule_type must be 'machine' or 'parameter'")
    if not rule.match_text.strip():
        raise HTTPException(status_code=400, detail="match_text is required")
    if rule.rule_type == "machine" and not rule.machine_id:
        raise HTTPException(status_code=400, detail="machine_id is required for a machine rule")
    if rule.rule_type == "parameter" and not rule.parameter:
        raise HTTPException(status_code=400, detail="parameter is required for a parameter rule")


@router.get("/")
def list_rules():
    try:
        return tag_mapping_service.list_rules()
    except Exception:
        logger.exception("Failed to list tag mapping rules")
        raise HTTPException(status_code=500, detail="Failed to list tag mapping rules")


@router.post("/")
def create_rule(rule: TagRule = Body(...)):
    _validate(rule)
    new_id = tag_mapping_service.create_rule(rule.model_dump())
    return {"id": new_id, "message": "Rule created"}


@router.put("/{rule_id}")
def update_rule(rule_id: int, rule: TagRule = Body(...)):
    _validate(rule)
    if not tag_mapping_service.update_rule(rule_id, rule.model_dump()):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule updated"}


@router.delete("/{rule_id}")
def delete_rule(rule_id: int):
    if not tag_mapping_service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}


@router.post("/reload")
async def reload_mapping():
    """Invalidate the rule cache and re-crawl OPC UA so new rules apply to tags."""
    tag_mapping_service.invalidate()
    try:
        from app.services.wincc_service import wincc_monitor
        await wincc_monitor.reconnect()
    except Exception as e:
        logger.warning(f"Remap reconnect failed (OPC UA may be offline): {e}")
        return {"message": "Rules reloaded; OPC UA not connected — will apply on next connect."}
    return {"message": "Rules reloaded and OPC UA re-crawled."}
