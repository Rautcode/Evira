"""Generate all three report types and render their cover + analytics pages."""
import os
from datetime import datetime, timedelta

SERVER = os.getenv("MSSQL_SERVER", "localhost,14333")
os.environ["MSSQL_SERVER"] = SERVER
os.environ.setdefault("JWT_SECRET", "e2e-types-secret")
os.environ.setdefault("MSSQL_DATABASE", "scada_reports")
os.environ.setdefault("MSSQL_AUTH_TYPE", "sql")
os.environ.setdefault("MSSQL_USERNAME", "sa")
os.environ.setdefault("MSSQL_PASSWORD", "Scada!Pass2026")
os.environ["MSSQL_ALLOWED_SERVERS"] = SERVER
os.environ.setdefault("SEED_DEMO_DATA", "1")

from fastapi.testclient import TestClient
from app.main import app
import fitz

end = datetime.now().date()
start = end - timedelta(days=20)
date_range = {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}

types = [
    ("production_summary", "production_summary"),
    ("downtime_analysis", "downtime_analysis"),
    ("quality_metrics", "quality_metrics"),
]

with TestClient(app) as client:
    r = client.post("/auth/login", json={
        "username": os.getenv("ADMIN_USERNAME", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
    })
    h = {"Authorization": f"Bearer {r.json()['token']}"}

    for rtype, tpl in types:
        resp = client.post("/report/generate", json={
            "date_range": date_range, "machine_id": "M001", "shift": "Full",
            "report_type": rtype, "template_id": tpl,
            "output_type": "pdf", "with_chart": True,
        }, headers=h)
        out = f"_type_{rtype}.pdf"
        with open(out, "wb") as f:
            f.write(resp.content)
        doc = fitz.open(out)
        # render cover (page 0) and analytics (page 2)
        for pidx, tag in [(0, "cover"), (2, "analytics")]:
            if pidx < doc.page_count:
                doc[pidx].get_pixmap(dpi=100).save(f"_type_{rtype}_{tag}.png")
        print(f"[OK] {rtype}: status={resp.status_code} bytes={len(resp.content)} pages={doc.page_count}")
        doc.close()
print("done")
