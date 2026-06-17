"""End-to-end smoke test against a live SQL Server.

Runs the real FastAPI app (TestClient triggers startup: DB init + seed + scheduler
+ wincc task), then exercises the core authenticated API surface. Intended to be
run with the containerized SQL Server up. Not part of the unit suite.
"""
import os

os.environ.setdefault("JWT_SECRET", "e2e-smoke-secret")
SERVER = os.getenv("MSSQL_SERVER", "localhost,14333")
os.environ["MSSQL_SERVER"] = SERVER
os.environ.setdefault("MSSQL_DATABASE", "scada_reports")
os.environ.setdefault("MSSQL_AUTH_TYPE", "sql")
os.environ.setdefault("MSSQL_USERNAME", "sa")
os.environ.setdefault("MSSQL_PASSWORD", "Scada!Pass2026")
os.environ["MSSQL_ALLOWED_SERVERS"] = SERVER
os.environ.setdefault("SEED_DEMO_DATA", "1")

from fastapi.testclient import TestClient
from app.main import app

results = []

def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

with TestClient(app) as client:
    # 1. Auth rejected without token
    r = client.get("/dashboard/stats")
    check("dashboard requires auth", r.status_code == 401, f"status={r.status_code}")

    # 2. Login with real SQL credentials
    r = client.post("/auth/login", json={
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
    })
    ok = r.status_code == 200 and r.json().get("token")
    check("login returns token", bool(ok), f"status={r.status_code}")
    token = r.json().get("token") if r.status_code == 200 else None
    h = {"Authorization": f"Bearer {token}"} if token else {}

    # 3a. /health (unauthenticated liveness probe)
    r = client.get("/health")
    check("/health unauthenticated", r.status_code == 200, f"status={r.status_code} body={r.text[:60]}")

    # 3b. /auth/me returns role field
    r = client.get("/auth/me", headers=h)
    body = r.json() if r.status_code == 200 else {}
    check("/auth/me returns role", r.status_code == 200 and "role" in body, f"status={r.status_code} keys={list(body.keys())}")

    # 4. Dashboard stats (real DB reads)
    r = client.get("/dashboard/stats", headers=h)
    ok = r.status_code == 200 and "system_status" in r.json()
    check("dashboard stats", ok, f"status={r.status_code}")

    # 5. SCADA tags
    r = client.get("/dashboard/scada/tags", headers=h)
    check("scada tags", r.status_code == 200, f"status={r.status_code} n={len(r.json()) if r.status_code==200 else '-'}")

    # 6. Machines (seeded -> expect 5)
    r = client.get("/report/machines", headers=h)
    n = len(r.json().get("data", {}).get("machines", [])) if r.status_code == 200 else 0
    check("report machines seeded", r.status_code == 200 and n >= 4, f"status={r.status_code} machines={n}")

    # 7. Report history list
    r = client.get("/report/list", headers=h)
    check("report list", r.status_code == 200, f"status={r.status_code}")

    # 8. Templates
    r = client.get("/template/", headers=h)
    check("templates list", r.status_code == 200, f"status={r.status_code} n={len(r.json()) if r.status_code==200 else '-'}")

    # 9. Scheduler list
    r = client.get("/scheduler/", headers=h)
    check("scheduler list", r.status_code == 200, f"status={r.status_code}")

    # 10. Path traversal blocked on chart download
    r = client.get("/charts/download/..%2f..%2fmain.py", headers=h)
    check("charts traversal blocked", r.status_code in (400, 404), f"status={r.status_code}")

    # 11. GET /users — admin token must succeed, operator token must get 403
    r = client.get("/users", headers=h)  # h is admin
    check("/users admin 200", r.status_code == 200, f"status={r.status_code}")

    op_login = client.post("/auth/login", json={"username": "operator", "password": "operator123"})
    if op_login.status_code == 200 and op_login.json().get("token"):
        op_h = {"Authorization": f"Bearer {op_login.json()['token']}"}
        r = client.get("/users", headers=op_h)
        check("/users operator 403", r.status_code == 403, f"status={r.status_code}")
    else:
        check("/users operator 403", False, "operator user not found — seed may need updating")

    # 12. GET /dashboard/alerts — returns a list (may be empty)
    r = client.get("/dashboard/alerts", headers=h)
    ok = r.status_code == 200 and isinstance(r.json(), list)
    check("dashboard alerts list", ok, f"status={r.status_code} type={type(r.json()).__name__ if r.status_code==200 else '-'}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== {passed}/{len(results)} checks passed ====")
raise SystemExit(0 if passed == len(results) else 1)
