import os
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from app.utils.db_connector import DBConnector
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import uuid

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

class ReportGenerator:
    def __init__(self, db_params: dict):
        self.db_params = db_params
        self.connector = DBConnector(**db_params)
        self.env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    def fetch_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        # Example: filters = {'start_date': ..., 'end_date': ..., 'machine_id': ..., 'type': ...}
        query = """
            SELECT * FROM logs
            WHERE machine_id = ?
            AND type = ?
            AND timestamp BETWEEN ? AND ?
        """
        conn = self.connector.get_connection()
        df = pd.read_sql(query, conn, params=[filters['machine_id'], filters['type'], filters['start_date'], filters['end_date']])
        conn.close()
        return df

    def render_template(self, template_id: str, context: dict) -> str:
        template_file = f"{template_id}.j2"
        template = self.env.get_template(template_file)
        return template.render(**context)

    def generate_chart(self, df: pd.DataFrame, chart_path: str) -> Optional[str]:
        if 'timestamp' in df.columns and 'value' in df.columns:
            plt.figure(figsize=(6,4))
            plt.plot(pd.to_datetime(df['timestamp']), df['value'])
            plt.title('Value over Time')
            plt.xlabel('Timestamp')
            plt.ylabel('Value')
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
            return chart_path
        return None

    def export_pdf(self, html_content: str, pdf_path: str, chart_path: Optional[str] = None):
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 12)
        textobject = c.beginText(40, height - 40)
        for line in html_content.splitlines():
            textobject.textLine(line)
        c.drawText(textobject)
        if chart_path and os.path.exists(chart_path):
            c.drawImage(chart_path, 40, 100, width=500, preserveAspectRatio=True, mask='auto')
        c.save()
        return pdf_path

    def export_csv(self, df: pd.DataFrame, csv_path: str):
        df.to_csv(csv_path, index=False)
        return csv_path

    def generate_report(self, filters: Dict[str, Any], template_id: str, with_chart: bool = False) -> Dict[str, str]:
        df = self.fetch_data(filters)
        context = {"data": df.to_dict(orient='records'), **filters}
        html_content = self.render_template(template_id, context)
        file_id = f"report_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chart_path = None
        if with_chart:
            chart_path = os.path.join(OUTPUT_DIR, f"{file_id}_chart.png")
            self.generate_chart(df, chart_path)
        pdf_path = os.path.join(OUTPUT_DIR, f"{file_id}.pdf")
        csv_path = os.path.join(OUTPUT_DIR, f"{file_id}.csv")
        self.export_pdf(html_content, pdf_path, chart_path)
        self.export_csv(df, csv_path)
        return {"pdf": pdf_path, "csv": csv_path, "chart": chart_path if chart_path else ""}
