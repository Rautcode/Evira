import os
import sys
from datetime import datetime, timedelta

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.report_service import ReportService
from app.utils.db_connector import DBConnector

def test_generate_report():
    print("Testing report generation with real data...")
    
    # 1. Verify DB Connection
    try:
        conn = DBConnector().get_connection()
        print("Database connection successful.")
        conn.close()
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    # 2. Setup parameters targeting the seeded data
    now = datetime.now()
    date_range = {
        "start": "2026-05-01 00:00:00",
        "end": "2026-06-30 23:59:59"
    }
    machine_id = "M001"  # Extruder Alpha
    shift = "Morning"
    report_type = "production_summary"
    
    # Ensure templates and reports directories exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'reports'), exist_ok=True)

    import json
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'test_template.json')
    if not os.path.exists(template_path):
        with open(template_path, 'w') as f:
            json.dump({
                "name": "Test Production Report",
                "category": "General",
                "description": "Test template",
                "content": {
                    "body": """
                    <html>
                        <body>
                            <h1>Test Production Report</h1>
                            <p>Machine: {{ machine_id }}</p>
                            <p>Shift: {{ shift }}</p>
                            <p>Report Type: {{ report_type }}</p>
                            <h3>Raw Telemetry Data</h3>
                            <table border="1">
                                <tr><th>Timestamp</th><th>Parameter</th><th>Value</th><th>Unit</th></tr>
                                {% for row in data[:50] %}
                                <tr>
                                    <td>{{ row.timestamp }}</td>
                                    <td>{{ row.parameter }}</td>
                                    <td>{{ row.value }}</td>
                                    <td>{{ row.unit }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </body>
                    </html>
                    """
                }
            }, f)
        print("Created test JSON template.")

    # 4. Generate the report
    service = ReportService()
    try:
        pdf_path = service.generate_report(
            date_range=date_range,
            machine_id=machine_id,
            shift=shift,
            report_type=report_type,
            template_id="test_template",
            output_type="pdf",
            with_chart=True
        )
        print(f"SUCCESS: Report successfully generated at: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        
    except Exception as e:
        print(f"FAILED to generate report: {e}")

if __name__ == "__main__":
    test_generate_report()
