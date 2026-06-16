"""Configurable OPC UA tag -> machine/parameter mapping.

Replaces the previously hardcoded heuristics with DB-backed rules so the app can
be pointed at any factory's WinCC naming without code changes. Rules are cached
and reloaded on write.
"""

import logging
import threading
from typing import Optional, List, Dict, Any

from app.utils.db import get_db_connection

logger = logging.getLogger(__name__)


class TagMappingService:
    def __init__(self):
        self._cache: Optional[Dict[str, list]] = None
        self._lock = threading.Lock()

    # ---- cache ----
    def invalidate(self) -> None:
        with self._lock:
            self._cache = None

    def _load(self) -> Dict[str, list]:
        rules: Dict[str, list] = {"machine": [], "parameter": []}
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT rule_type, match_text, machine_id, parameter, unit "
                    "FROM tag_mapping_rules WHERE active = 1 "
                    "ORDER BY priority ASC, id ASC"
                )
                for row in cur.fetchall():
                    rt = (row.rule_type or "").lower()
                    match = (row.match_text or "").lower()
                    if not match:
                        continue
                    if rt == "machine":
                        rules["machine"].append({"match": match, "machine_id": row.machine_id})
                    elif rt == "parameter":
                        rules["parameter"].append(
                            {"match": match, "parameter": row.parameter, "unit": row.unit}
                        )
            finally:
                cur.close()
        return rules

    def get_rules(self) -> Dict[str, list]:
        with self._lock:
            if self._cache is None:
                try:
                    self._cache = self._load()
                except Exception as e:
                    logger.error(f"Failed to load tag mapping rules: {e}")
                    return {"machine": [], "parameter": []}
            return self._cache

    # ---- matching (used by the OPC UA discovery) ----
    def match_machine(self, text: str) -> Optional[str]:
        text = (text or "").lower()
        for r in self.get_rules()["machine"]:
            if r["match"] in text:
                return r["machine_id"]
        return None

    def match_parameter(self, text: str) -> Optional[Dict[str, Any]]:
        text = (text or "").lower()
        for r in self.get_rules()["parameter"]:
            if r["match"] in text:
                return {"parameter": r["parameter"], "unit": r["unit"]}
        return None

    # ---- CRUD (used by the API) ----
    def list_rules(self) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT id, rule_type, match_text, machine_id, parameter, unit, priority, active "
                    "FROM tag_mapping_rules ORDER BY rule_type, priority ASC, id ASC"
                )
                return [
                    {
                        "id": row.id,
                        "rule_type": row.rule_type,
                        "match_text": row.match_text,
                        "machine_id": row.machine_id,
                        "parameter": row.parameter,
                        "unit": row.unit,
                        "priority": row.priority,
                        "active": bool(row.active),
                    }
                    for row in cur.fetchall()
                ]
            finally:
                cur.close()

    def create_rule(self, data: Dict[str, Any]) -> int:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO tag_mapping_rules (rule_type, match_text, machine_id, parameter, unit, priority, active) "
                    "OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?)",
                    data["rule_type"], data["match_text"], data.get("machine_id"),
                    data.get("parameter"), data.get("unit"),
                    int(data.get("priority", 100)), 1 if data.get("active", True) else 0,
                )
                new_id = cur.fetchone()[0]
                conn.commit()
            finally:
                cur.close()
        self.invalidate()
        return new_id

    def update_rule(self, rule_id: int, data: Dict[str, Any]) -> bool:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE tag_mapping_rules SET match_text=?, machine_id=?, parameter=?, unit=?, priority=?, active=? "
                    "WHERE id=?",
                    data["match_text"], data.get("machine_id"), data.get("parameter"),
                    data.get("unit"), int(data.get("priority", 100)),
                    1 if data.get("active", True) else 0, rule_id,
                )
                affected = cur.rowcount
                conn.commit()
            finally:
                cur.close()
        self.invalidate()
        return affected > 0

    def delete_rule(self, rule_id: int) -> bool:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM tag_mapping_rules WHERE id=?", rule_id)
                affected = cur.rowcount
                conn.commit()
            finally:
                cur.close()
        self.invalidate()
        return affected > 0


tag_mapping_service = TagMappingService()
