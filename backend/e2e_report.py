"""End-to-end report-generation test against the live SQL Server.

Drives /report/generate for both PDF and CSV and verifies real files come back.
"""
import os
from datetime import datetime, timedelta

SERVER = os.getenv("MSSQL_SERVER", "localhost,14333")
os.environ["MSSQL_SERVER"] = SERVER
os.environ.setdefault("JWT_SECRET", "e2e-report-secret")
os.environ.setdefault("MSSQL_DATABASE", "scada_reports")
os.environ.setdefault("MSSQL_AUTH_TYPE", "sql")
os.environ.setdefault("MSSQL_USERNAME", "sa")
os.environ.setdefault("MSSQL_PASSWORD", "Scada!Pass2026")
os.environ["MSSQL_ALLOWED_SERVERS"] = SERVER
os.environ.setdefault("SEED_DEMO_DATA", "1")

from fastapi.testclient import TestClient
from app.main import app

end = datetime.now().date()
start = end - timedelta(days=20)
date_range = {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

with TestClient(app) as client:
    r = client.post("/auth/login", json={
        "auth_type": "sql", "server": SERVER, "database": "scada_reports",
        "username": "sa", "password": os.environ["MSSQL_PASSWORD"],
    })
    token = r.json().get("token")
    h = {"Authorization": f"Bearer {token}"}
    check("login", bool(token))

    base = {"date_range": date_range, "machine_id": "M001", "shift": "Full",
            "report_type": "production_summary", "template_id": "production_summary"}

    # PDF with chart
    r = client.post("/report/generate", json={**base, "output_type": "pdf", "with_chart": True}, headers=h)
    pdf_ok = r.status_code == 200 and r.content[:5] == b"%PDF-"
    check("generate PDF (with chart)", pdf_ok, f"status={r.status_code} bytes={len(r.content)} magic={r.content[:5]!r}")
    if pdf_ok:
        with open("e2e_report_out.pdf", "wb") as f:
            f.write(r.content)

    # CSV
    r = client.post("/report/generate", json={**base, "output_type": "csv", "with_chart": False}, headers=h)
    csv_ok = r.status_code == 200 and len(r.content) > 0
    head = r.content[:80].decode("utf-8", "replace").replace("\n", " ")
    check("generate CSV", csv_ok, f"status={r.status_code} bytes={len(r.content)} head='{head}'")

    # History recorded
    r = client.get("/report/list", headers=h)
    n = len(r.json()) if r.status_code == 200 else 0
    check("report history recorded", r.status_code == 200 and n >= 1, f"history rows={n}")

passed = sum(results)
print(f"\n==== {passed}/{len(results)} report checks passed ====")
raise SystemExit(0 if passed == len(results) else 1)
