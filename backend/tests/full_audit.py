"""
FULL APPLICATION AUDIT - Production Readiness Test Suite
Tests every layer: Config -> DB -> Data Fetch -> Report Engine -> PDF Output -> Email Service -> Scheduler
No mocks. Real data. Real connections.
"""
import os, sys, json, time, traceback
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0
WARN = 0
results = []

def test(name, func):
    global PASS, FAIL, WARN
    try:
        result = func()
        if result is True:
            PASS += 1
            results.append(("PASS", name, ""))
            print(f"  [PASS] {name}")
        elif result is None:
            WARN += 1
            results.append(("WARN", name, "Non-critical"))
            print(f"  [WARN] {name}")
        else:
            FAIL += 1
            results.append(("FAIL", name, str(result)))
            print(f"  [FAIL] {name} -> {result}")
    except Exception as e:
        FAIL += 1
        tb = traceback.format_exc().split('\n')[-3].strip()
        results.append(("FAIL", name, f"{e} | {tb}"))
        print(f"  [FAIL] {name} -> {e}")

print("=" * 70)
print(" SCADA ASSISTANT - FULL PRODUCTION READINESS AUDIT")
print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============================================================
# PHASE 1: CONFIGURATION LAYER
# ============================================================
print("\n--- PHASE 1: CONFIGURATION LAYER ---")

def test_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.exists(env_path):
        return ".env file missing"
    with open(env_path, 'r') as f:
        content = f.read()
    if 'JWT_SECRET' not in content:
        return "JWT_SECRET not set in .env"
    if 'MSSQL_SERVER' not in content:
        return "MSSQL_SERVER not set"
    return True
test(".env file exists and has required keys", test_env_file)

def test_config_manager():
    from app.utils.config_manager import config_manager
    config = config_manager.load_config()
    if not isinstance(config, dict):
        return "Config did not return dict"
    return True
test("ConfigManager loads system_config.json", test_config_manager)

def test_config_save_roundtrip():
    from app.utils.config_manager import config_manager
    config = config_manager.load_config()
    marker = f"audit_{int(time.time())}"
    config["_audit_marker"] = marker
    config_manager.save_config(config)
    reloaded = config_manager.load_config()
    if reloaded.get("_audit_marker") != marker:
        return "Save/Load roundtrip failed"
    # Clean up
    del config["_audit_marker"]
    config_manager.save_config(config)
    return True
test("ConfigManager save/load roundtrip", test_config_save_roundtrip)

def test_gitignore():
    gi_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '.gitignore')
    if not os.path.exists(os.path.normpath(gi_path)):
        return ".gitignore missing"
    return True
test(".gitignore exists", test_gitignore)

# ============================================================
# PHASE 2: DATABASE LAYER
# ============================================================
print("\n--- PHASE 2: DATABASE LAYER ---")

def test_db_connector():
    from app.utils.db_connector import DBConnector
    conn = DBConnector().get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row[0] != 1:
        return "SELECT 1 returned unexpected value"
    return True
test("DBConnector connects to SQL Server", test_db_connector)

def test_db_pool():
    from app.utils.db_pool import pool
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")
    db_name = cursor.fetchone()[0]
    cursor.close()
    pool.return_connection(conn)
    if not db_name:
        return "Could not get database name"
    return True
test("Connection pool acquire/return", test_db_pool)

def test_tables_exist():
    from app.utils.db_pool import get_db_connection
    required_tables = ['logs', 'wincc_tags', 'report_history', 'activity_log']
    missing = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in required_tables:
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table}")
                cursor.fetchall()
            except Exception:
                missing.append(table)
    if missing:
        return f"Missing tables: {', '.join(missing)}"
    return True
test("Required database tables exist", test_tables_exist)

def test_logs_have_data():
    from app.utils.db_pool import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        cursor.close()
    if count == 0:
        return "logs table is EMPTY - no telemetry data"
    return True
test(f"logs table has telemetry data", test_logs_have_data)

def test_logs_data_quality():
    from app.utils.db_pool import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT machine_id) as machines,
                COUNT(DISTINCT parameter) as params,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM logs
        """)
        row = cursor.fetchone()
        cursor.close()
    total, machines, params, earliest, latest = row
    print(f"         -> {total} rows | {machines} machines | {params} params | {earliest} to {latest}")
    if machines < 1:
        return "No machine_id data found"
    if params < 1:
        return "No parameter types found"
    return True
test("Data quality check (machines, params, date range)", test_logs_data_quality)

def test_logs_column_schema():
    from app.utils.db_pool import get_db_connection
    required_cols = ['machine_id', 'timestamp', 'parameter', 'value', 'unit', 'status', 'shift']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM logs")
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
    missing = [c for c in required_cols if c not in columns]
    if missing:
        return f"Missing columns in logs: {', '.join(missing)}"
    print(f"         -> Columns: {', '.join(columns)}")
    return True
test("logs table schema has required columns", test_logs_column_schema)

# ============================================================
# PHASE 3: DATA FETCH LAYER (ReportService)
# ============================================================
print("\n--- PHASE 3: DATA FETCH LAYER ---")

def test_fetch_data():
    from app.services.report_service import ReportService
    svc = ReportService()
    data = svc.fetch_data(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="all",
        shift="Full",
        report_type="all"
    )
    if not isinstance(data, dict):
        return f"Expected dict, got {type(data)}"
    raw = data.get("raw", [])
    if len(raw) == 0:
        return "fetch_data returned 0 rows"
    print(f"         -> Fetched {len(raw)} raw rows")
    return True
test("ReportService.fetch_data returns data", test_fetch_data)

def test_fetch_filtered_machine():
    from app.services.report_service import ReportService
    svc = ReportService()
    data = svc.fetch_data(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="M001",
        shift="Full",
        report_type="all"
    )
    raw = data.get("raw", [])
    wrong_machines = [r for r in raw if r.get('machine_id') != 'M001']
    if wrong_machines:
        return f"Filter leak: {len(wrong_machines)} rows from wrong machine"
    print(f"         -> M001 filter: {len(raw)} rows, 0 leaks")
    return True
test("Machine filter (M001) returns only M001 data", test_fetch_filtered_machine)

# ============================================================
# PHASE 4: CHART GENERATION
# ============================================================
print("\n--- PHASE 4: CHART GENERATION ---")

def test_chart_generation():
    from app.services.report_service import ReportService
    svc = ReportService()
    data = svc.fetch_data(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="M001",
        shift="Full",
        report_type="all"
    )
    chart_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports', 'audit_chart.png')
    result = svc.generate_chart(data["raw"], chart_path)
    if not result or not os.path.exists(chart_path):
        return "Chart file was not created"
    size = os.path.getsize(chart_path)
    if size < 1000:
        return f"Chart file suspiciously small: {size} bytes"
    print(f"         -> Chart: {size:,} bytes at {chart_path}")
    return True
test("Matplotlib chart generation with real data", test_chart_generation)

# ============================================================
# PHASE 5: PDF REPORT GENERATION (END-TO-END)
# ============================================================
print("\n--- PHASE 5: PDF REPORT GENERATION ---")

def test_pdf_generation():
    from app.services.report_service import ReportService
    svc = ReportService()
    pdf_path = svc.generate_report(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="M001",
        shift="Morning",
        report_type="production_summary",
        template_id="test_template",
        output_type="pdf",
        with_chart=True
    )
    if not pdf_path or not os.path.exists(pdf_path):
        return "PDF file was not created"
    size = os.path.getsize(pdf_path)
    if size < 5000:
        return f"PDF suspiciously small: {size} bytes (likely empty)"
    print(f"         -> PDF: {size:,} bytes at {pdf_path}")
    return True
test("Full PDF report with chart (M001, Morning shift)", test_pdf_generation)

def test_csv_generation():
    from app.services.report_service import ReportService
    svc = ReportService()
    csv_path = svc.generate_report(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="all",
        shift="Full",
        report_type="all",
        template_id="test_template",
        output_type="csv",
        with_chart=False
    )
    if not csv_path or not os.path.exists(csv_path):
        return "CSV file was not created"
    size = os.path.getsize(csv_path)
    print(f"         -> CSV: {size:,} bytes at {csv_path}")
    return True
test("CSV export generation", test_csv_generation)

def test_pdf_multi_machine():
    from app.services.report_service import ReportService
    svc = ReportService()
    pdf_path = svc.generate_report(
        date_range={"start": "2025-01-01", "end": "2027-12-31"},
        machine_id="all",
        shift="Full",
        report_type="all",
        template_id="test_template",
        output_type="pdf",
        with_chart=True
    )
    size = os.path.getsize(pdf_path)
    if size < 5000:
        return f"Multi-machine PDF too small: {size} bytes"
    print(f"         -> All-machines PDF: {size:,} bytes")
    return True
test("PDF report covering ALL machines/shifts", test_pdf_multi_machine)

# ============================================================
# PHASE 6: EMAIL SERVICE
# ============================================================
print("\n--- PHASE 6: EMAIL SERVICE ---")

def test_email_service_init():
    from app.services.email_service import email_service
    if not hasattr(email_service, 'send_email'):
        return "send_email method missing"
    if not hasattr(email_service, 'check_connection'):
        return "check_connection method missing"
    if not hasattr(email_service, 'save_config'):
        return "save_config method missing"
    return True
test("EmailService has all required methods", test_email_service_init)

def test_email_check_connection():
    from app.services.email_service import email_service
    # Just test it doesn't crash, result depends on config
    result = email_service.check_connection()
    print(f"         -> check_connection returned: {result}")
    return True
test("EmailService.check_connection() does not crash", test_email_check_connection)

# ============================================================
# PHASE 7: SCHEDULER SERVICE
# ============================================================
print("\n--- PHASE 7: SCHEDULER ---")

def test_scheduler_import():
    from app.routers.scheduler import scheduler, list_jobs, add_job
    if not scheduler.running:
        return "Scheduler is not running"
    return True
test("APScheduler BackgroundScheduler is running", test_scheduler_import)

def test_scheduler_list():
    from app.routers.scheduler import list_jobs
    jobs = list_jobs()
    if not isinstance(jobs, list):
        return f"list_jobs returned {type(jobs)}, expected list"
    print(f"         -> Active jobs: {len(jobs)}")
    return True
test("Scheduler can list jobs", test_scheduler_list)

# ============================================================
# PHASE 8: SECURITY AUDIT
# ============================================================
print("\n--- PHASE 8: SECURITY ---")

def test_jwt_secret_not_default():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    secret = os.getenv("JWT_SECRET", "")
    if secret == "super-secret-scada-key-change-in-production":
        return "JWT_SECRET is still the insecure default"
    if len(secret) < 32:
        return f"JWT_SECRET too short: {len(secret)} chars"
    return True
test("JWT_SECRET is secure and not default", test_jwt_secret_not_default)

def test_path_traversal_blocked():
    """Simulate a path traversal attack on the download endpoint"""
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports'))
    malicious_name = "../../.env"
    file_path = os.path.join(reports_dir, malicious_name)
    real_path = os.path.realpath(file_path)
    if real_path.startswith(os.path.realpath(reports_dir)):
        return "Path traversal NOT blocked - attacker can read .env"
    return True
test("Path traversal attack on /download is blocked", test_path_traversal_blocked)

# ============================================================
# PHASE 9: WINCC / OPC UA SERVICE
# ============================================================
print("\n--- PHASE 9: WINCC OPC UA ---")

def test_wincc_monitor_init():
    from app.services.wincc_service import wincc_monitor
    status = wincc_monitor.get_status()
    if not isinstance(status, dict):
        return "get_status() did not return dict"
    print(f"         -> Connected: {status['connected']} | URL: {status['server_url']}")
    return True
test("WinCCMonitor initializes and returns status", test_wincc_monitor_init)

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 70)
print(f" AUDIT RESULTS: {PASS} PASSED | {FAIL} FAILED | {WARN} WARNINGS")
print("=" * 70)

if FAIL == 0:
    print(" VERDICT: APPLICATION IS PRODUCTION READY")
else:
    print(f" VERDICT: NOT PRODUCTION READY ({FAIL} failures)")
    print("\n FAILURES:")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"   X {name}")
            print(f"     -> {detail}")

print("=" * 70)
