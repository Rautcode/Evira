"""Configurable OPC UA tag -> machine/parameter mapping.

Replaces the previously hardcoded heuristics with DB-backed rules so the app can
be pointed at any factory's WinCC naming without code changes. Rules are cached
and reloaded on write.
"""

import re
import logging
import threading
from typing import Optional, List, Dict, Any

from app.utils.db import get_db_connection

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set:
    """Split a tag name into lowercase word tokens.

    Splits on non-alphanumerics AND camelCase / letter-digit boundaries so
    'Packaging_Delta_ErrorRate' -> {packaging, delta, error, rate}. This lets
    rule words match as whole tokens (so 'pack' no longer matches 'Packaging').
    """
    if not text:
        return set()
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    spaced = re.sub(r"(?<=[A-Za-z])(?=[0-9])", " ", spaced)
    spaced = re.sub(r"(?<=[0-9])(?=[A-Za-z])", " ", spaced)
    return {t for t in re.split(r"[^a-z0-9]+", spaced.lower()) if t}


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
    @staticmethod
    def _matches(match: str, tokens: set, text_lower: str) -> bool:
        # Multi-word rules (space-separated phrases) fall back to substring
        # match on the full lowercased text.
        if " " in match:
            return match in text_lower
        # Tokenize the rule itself so that alphanumeric names like "rx100" or
        # "m001" split the same way as tag names do (rx100→{rx,100}).
        # Then require every rule token to be present in the tag token set.
        # This prevents "pack" matching "Packaging" AND ensures "rx100" matches
        # "RX100_Temperature" but not "RX200_Temperature".
        rule_tokens = _tokenize(match)
        if not rule_tokens:
            return False
        return rule_tokens <= tokens

    def match_machine(self, text: str) -> Optional[str]:
        text_lower = (text or "").lower()
        tokens = _tokenize(text)
        for r in self.get_rules()["machine"]:
            if self._matches(r["match"], tokens, text_lower):
                return r["machine_id"]
        return None

    def match_parameter(self, text: str) -> Optional[Dict[str, Any]]:
        text_lower = (text or "").lower()
        tokens = _tokenize(text)
        for r in self.get_rules()["parameter"]:
            if self._matches(r["match"], tokens, text_lower):
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
