"""Verify configurable tag mapping: migration, seed, matching, word-boundary, and CRUD API."""
import os

SERVER = os.getenv("MSSQL_SERVER", "localhost,14333")
os.environ["MSSQL_SERVER"] = SERVER
os.environ.setdefault("JWT_SECRET", "e2e-tagmap-secret")
os.environ.setdefault("MSSQL_DATABASE", "scada_reports")
os.environ.setdefault("MSSQL_AUTH_TYPE", "sql")
os.environ.setdefault("MSSQL_USERNAME", "sa")
os.environ.setdefault("MSSQL_PASSWORD", "Scada!Pass2026")
os.environ["MSSQL_ALLOWED_SERVERS"] = SERVER

from app.services.tag_mapping_service import _tokenize, tag_mapping_service
from fastapi.testclient import TestClient
from app.main import app

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

# ── 1. Unit-level tokenizer tests (no DB) ───────────────────────────────────
toks = _tokenize("Packaging_Delta_ErrorRate")
check("tokenize: Packaging_Delta_ErrorRate", toks == {"packaging", "delta", "error", "rate"}, str(toks))

toks = _tokenize("ErrorRate")
check("tokenize: camelCase split", toks == {"error", "rate"}, str(toks))

toks = _tokenize("Zone1_Temp")
check("tokenize: digit boundary", "zone" in toks and "1" in toks and "temp" in toks, str(toks))

check("tokenize: empty string", _tokenize("") == set())

# Alphanumeric rule tokenization — "rx100" must split to {rx, 100}
toks = _tokenize("rx100")
check("tokenize: rx100 -> {rx, 100}", toks == {"rx", "100"}, str(toks))

# Verify _matches uses subset logic for alphanumeric rules
from app.services.tag_mapping_service import TagMappingService
_m = TagMappingService._matches
check("_matches: rx100 matches RX100_Temp", _m("rx100", _tokenize("RX100_Temperature"), "rx100_temperature"), "")
check("_matches: rx100 does NOT match RX200_Temp", not _m("rx100", _tokenize("RX200_Temperature"), "rx200_temperature"), "")

# ── 2. Seed data + default matching ─────────────────────────────────────────
tag_mapping_service.invalidate()
rules = tag_mapping_service.get_rules()
check("seeded machine rules", len(rules["machine"]) >= 5, f"count={len(rules['machine'])}")
check("seeded parameter rules", len(rules["parameter"]) >= 5, f"count={len(rules['parameter'])}")

check("extruder->M001", tag_mapping_service.match_machine("Extruder_01 Line A") == "M001")
check("temp->Temperature", (tag_mapping_service.match_parameter("Zone1_Temp") or {}).get("parameter") == "Temperature")
check("unknown tag -> no match", tag_mapping_service.match_machine("RX-9000-foo") is None)

# ── 3. Word-boundary regression: "pack" must NOT match "Packaging_…" ────────
with TestClient(app) as client:
    r = client.post("/auth/login", json={
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
    })
    h = {"Authorization": f"Bearer {r.json()['token']}"}

    # Inject a "pack" parameter rule at high priority
    r = client.post("/tag-mapping/", headers=h, json={
        "rule_type": "parameter", "match_text": "pack",
        "parameter": "Pack Count", "unit": "pcs", "priority": 1, "active": True,
    })
    check("create 'pack' rule", r.status_code == 200, f"status={r.status_code}")
    pack_id = r.json().get("id")

    tag_mapping_service.invalidate()
    matched = tag_mapping_service.match_parameter("Packaging_Delta_ErrorRate")
    check(
        "'pack' does NOT match 'Packaging_Delta_ErrorRate' (word-boundary)",
        matched is None or matched.get("parameter") != "Pack Count",
        f"got={matched}",
    )

    matched_exact = tag_mapping_service.match_parameter("Pack_Count")
    check(
        "'pack' DOES match 'Pack_Count' (exact token)",
        matched_exact is not None and matched_exact.get("parameter") == "Pack Count",
        f"got={matched_exact}",
    )

    # cleanup pack rule
    if pack_id:
        client.delete(f"/tag-mapping/{pack_id}", headers=h)

    # ── 4. CRUD: add custom machine rule, verify match, delete ───────────────
    r = client.get("/tag-mapping/", headers=h)
    check("API list rules", r.status_code == 200, f"status={r.status_code} n={len(r.json()) if r.status_code==200 else '-'}")

    r = client.post("/tag-mapping/", headers=h, json={
        "rule_type": "machine", "match_text": "rx100", "machine_id": "M001", "priority": 5,
    })
    check("API create rule", r.status_code == 200, f"status={r.status_code}")
    rule_id = r.json().get("id")

    tag_mapping_service.invalidate()
    check("custom rule matches after invalidate",
          tag_mapping_service.match_machine("RX100_Pump_Temp") == "M001")

    r = client.post("/tag-mapping/", headers=h, json={"rule_type": "bogus", "match_text": "x"})
    check("API rejects bad rule_type", r.status_code == 400, f"status={r.status_code}")

    r = client.delete(f"/tag-mapping/{rule_id}", headers=h)
    check("API delete rule", r.status_code == 200, f"status={r.status_code}")

    tag_mapping_service.invalidate()

passed = sum(results)
print(f"\n==== {passed}/{len(results)} tag-mapping checks passed ====")
raise SystemExit(0 if passed == len(results) else 1)
