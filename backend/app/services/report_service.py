from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from app.utils.db_connector import DBConnector
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from fpdf import FPDF
import csv
import logging

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../reports'))

class ReportService:
    def __init__(self, db_params: Optional[dict] = None):
        self.db_params = db_params or {}
        self.connector = DBConnector(**self.db_params)

    def fetch_data(self, date_range: Dict[str, str], machine_id: str, shift: str, report_type: str) -> List[Dict[str, Any]]:
        conditions = ["timestamp BETWEEN ? AND ?"]
        params = [date_range['start'], date_range['end']]
        
        # 'all' means no machine filter
        if machine_id and machine_id.lower() != 'all':
            conditions.append("machine_id = ?")
            params.append(machine_id)
            
        # 'full' means no shift filter
        if shift and shift.lower() != 'full':
            conditions.append("shift = ?")
            params.append(shift)
            
        # Handle report type mapping if needed, otherwise filter by it
        if report_type and report_type.lower() != 'all':
            conditions.append("report_type = ?")
            params.append(report_type)

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM logs WHERE {where_clause} ORDER BY timestamp ASC"
        
        conn = self.connector.get_connection()
        try:
            df = pd.read_sql(query, conn, params=params)
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Ensure robust mapping of values
                if 'value' in df.columns:
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
        finally:
            conn.close()
        
        raw_data = df.to_dict(orient='records')
        
        # Try to pivot data for electrical metrics (Voltage, Current, Energy, PF, Frequency)
        pivoted_data = []
        if not df.empty and 'parameter' in df.columns and 'value' in df.columns:
            try:
                pivot_df = df.pivot_table(
                    index=['timestamp', 'machine_id'], 
                    columns='parameter', 
                    values='value', 
                    aggfunc='first'
                ).reset_index()
                
                # Ensure specific columns exist to prevent Jinja errors
                for col in ['Voltage', 'Current', 'Energy', 'PF', 'Frequency']:
                    if col not in pivot_df.columns:
                        pivot_df[col] = None
                        
                # Convert timestamps to string for JSON serialization
                pivot_df['timestamp'] = pivot_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                pivoted_data = pivot_df.to_dict(orient='records')
            except Exception as e:
                logger.error(f"Failed to pivot data: {e}")
                
        return {
            "raw": raw_data,
            "pivoted": pivoted_data
        }

    def render_template(self, template_id: str, context: dict) -> str:
        from app.services.template_service import TemplateService
        ts = TemplateService()
        return ts.render_template(template_id, context)

    def generate_chart(self, data: List[Dict[str, Any]], chart_path: str) -> str:
        if not data:
            return ''
            
        df = pd.DataFrame(data)
        if 'timestamp' not in df.columns or 'value' not in df.columns or 'parameter' not in df.columns:
            return ''
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create a 1x2 subplot dashboard
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 1. Parameter Line Chart
        parameters = df['parameter'].unique()
        for param in parameters:
            param_data = df[df['parameter'] == param].sort_values('timestamp')
            # Normalize to first value just for trend visibility, or plot actuals if scales are similar
            # For simplicity, plotting actual values but standardizing the line width
            ax1.plot(param_data['timestamp'], param_data['value'], label=param, linewidth=2, marker='o', markersize=3)
            
        ax1.set_title('Telemetry Trends Over Time', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Value')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(loc='best', fontsize=8)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 2. Status Pie Chart
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            colors = ['#4CAF50' if s.lower() == 'normal' else '#FF5252' if s.lower() in ['warning', 'error'] else '#FFC107' for s in status_counts.index]
            ax2.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=colors, shadow=True)
            ax2.set_title('Machine Status Distribution', fontsize=12, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'No Status Data', horizontalalignment='center', verticalalignment='center')
            
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        return chart_path

    def generate_pdf(self, context: dict, pdf_path: str, chart_path: str = None):
        data = context.get('data', [])
        
        class EnterpriseSCADAPDF(FPDF):
            def header(self):
                # We don't want a generic header on the cover page
                if self.page_no() == 1:
                    return
                    
                # Corporate Header Banner for content pages (Primary Color Blue #0f172a)
                self.set_fill_color(15, 23, 42)
                self.rect(0, 0, 210, 20, 'F')
                
                self.set_text_color(255, 255, 255)
                self.set_font("helvetica", "B", 14)
                self.set_y(8)
                self.set_x(10)
                self.cell(0, 0, "SCADA ASSISTANT", new_x="RIGHT", new_y="TOP")
                self.set_font("helvetica", "", 8)
                self.set_x(10)
                self.set_y(13)
                self.cell(0, 0, "ENTERPRISE TELEMETRY REPORT", new_x="RIGHT", new_y="TOP")
                self.set_y(25)

            def footer(self):
                # Confidential Footer
                self.set_y(-15)
                self.set_draw_color(224, 224, 224)
                self.line(10, self.get_y(), 200, self.get_y())
                
                self.set_text_color(128, 128, 128)
                self.set_font("helvetica", "", 8)
                self.set_x(10)
                self.cell(0, 10, "CONFIDENTIAL - AUTOMATICALLY GENERATED BY SCADA REPORT ENGINE", new_x="RIGHT", new_y="TOP")
                self.set_x(0)
                self.cell(0, 10, f"Page {self.page_no()} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="R", new_x="RIGHT", new_y="TOP")

        pdf = EnterpriseSCADAPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        # --- 1. COVER PAGE ---
        pdf.set_fill_color(30, 64, 175) # Deep Blue Box
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_y(80)
        pdf.set_font("helvetica", "B", 36)
        report_title = context.get('report_type', 'System').replace('_', ' ').title()
        pdf.cell(0, 15, f"{report_title} Report", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 14)
        pdf.set_y(105)
        pdf.cell(0, 10, f"Machine Target: {context.get('machine_id', 'All')}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"Shift Segment: {context.get('shift', 'All')}", align="C", new_x="LMARGIN", new_y="NEXT")
        
        date_range = context.get('date_range', {})
        pdf.set_font("helvetica", "I", 12)
        pdf.set_y(130)
        pdf.cell(0, 10, f"Data Period: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_y(250)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, "Generated by SCADA Assistant Enterprise Engine", align="C", new_x="LMARGIN", new_y="NEXT")

        # --- 2. EXECUTIVE SUMMARY (KPIs) ---
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        if data:
            df = pd.DataFrame(data)
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
            total_records = len(df)
            warnings = int(df['status'].str.lower().isin(['warning', 'error']).sum()) if 'status' in df.columns else 0
            normal_rate = (1 - warnings / total_records) * 100 if total_records else 0.0
            n_params = int(df['parameter'].nunique()) if 'parameter' in df.columns else 0

            # KPI grid: four cards across the page
            cards = [
                ("Total Log Entries", str(total_records), (15, 23, 42)),
                ("Anomalies / Warnings", str(warnings), (220, 38, 38) if warnings else (22, 163, 74)),
                ("Normal Rate", f"{normal_rate:.1f}%", (22, 163, 74) if normal_rate >= 90 else (202, 138, 4)),
                ("Parameters Tracked", str(n_params), (15, 23, 42)),
            ]
            card_w, card_h, gap, x0, y0 = 44, 28, 4, 10, 40
            for i, (label, value, color) in enumerate(cards):
                x = x0 + i * (card_w + gap)
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(x, y0, card_w, card_h, 'FD')
                pdf.set_xy(x, y0 + 4)
                pdf.set_text_color(100, 116, 139)
                pdf.set_font("helvetica", "B", 8)
                pdf.multi_cell(card_w, 4, label.upper(), align="C")
                pdf.set_xy(x, y0 + 16)
                pdf.set_text_color(*color)
                pdf.set_font("helvetica", "B", 20)
                pdf.cell(card_w, 8, value, align="C")

            pdf.set_text_color(0, 0, 0)
            pdf.set_y(y0 + card_h + 12)

            # Parameter statistics table (count / min / avg / max per parameter)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, "Parameter Statistics", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            if 'value' in df.columns and 'parameter' in df.columns:
                stats = df.groupby('parameter')['value'].agg(['count', 'min', 'mean', 'max']).reset_index()
                widths = [55, 25, 30, 30, 30, 20]
                headers = ["Parameter", "Count", "Min", "Average", "Max", "Unit"]
                pdf.set_fill_color(30, 64, 175)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 10)
                for w, htxt in zip(widths, headers):
                    pdf.cell(w, 8, htxt, border=1, fill=True, align="C")
                pdf.ln()
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("helvetica", "", 10)
                fill = False
                for _, row in stats.iterrows():
                    unit = ''
                    if 'unit' in df.columns:
                        us = df[df['parameter'] == row['parameter']]['unit']
                        unit = str(us.iloc[0]) if len(us) else ''
                    pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                    pdf.cell(widths[0], 8, str(row['parameter']), border=1, fill=fill)
                    pdf.cell(widths[1], 8, str(int(row['count'])), border=1, fill=fill, align="C")
                    pdf.cell(widths[2], 8, f"{row['min']:.2f}", border=1, fill=fill, align="R")
                    pdf.cell(widths[3], 8, f"{row['mean']:.2f}", border=1, fill=fill, align="R")
                    pdf.cell(widths[4], 8, f"{row['max']:.2f}", border=1, fill=fill, align="R")
                    pdf.cell(widths[5], 8, unit, border=1, fill=fill, align="C")
                    pdf.ln()
                    fill = not fill

            # Context strip
            pdf.ln(6)
            dr = context.get('date_range', {})
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 6, f"Reporting period: {dr.get('start', 'N/A')} to {dr.get('end', 'N/A')}    |    "
                            f"Machine: {context.get('machine_id', 'All')}    |    Shift: {context.get('shift', 'All')}",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 10, "No data available for the selected timeframe.", new_x="LMARGIN", new_y="NEXT")
            
        # --- 3. ADVANCED ANALYTICS (CHARTS) ---
        if chart_path and os.path.exists(chart_path):
            pdf.add_page()
            pdf.set_font("helvetica", "B", 18)
            pdf.cell(0, 10, "Visual Analytics", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.image(chart_path, x=10, w=190)

        # --- 4. RAW DATA LOGS ---
        if data:
            pdf.add_page()
            pdf.set_font("helvetica", "B", 18)
            pdf.cell(0, 10, "Telemetry Log Data", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            # Table Header
            pdf.set_fill_color(30, 64, 175)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(45, 8, "Timestamp", border=1, fill=True)
            pdf.cell(45, 8, "Parameter", border=1, fill=True)
            pdf.cell(30, 8, "Value", border=1, fill=True)
            pdf.cell(20, 8, "Unit", border=1, fill=True)
            pdf.cell(40, 8, "Status", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            
            # Table Body
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            fill = False
            for row in data[:200]: # Cap at 200 rows to prevent massive PDFs during preview
                pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                
                # Check status for coloring
                status = str(row.get('status', ''))
                if status.lower() in ['warning', 'error']:
                    pdf.set_text_color(220, 38, 38)
                    pdf.set_font("helvetica", "B", 9)
                else:
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("helvetica", "", 9)
                    
                pdf.cell(45, 8, str(row.get('timestamp', ''))[:19], border=1, fill=fill)
                pdf.cell(45, 8, str(row.get('parameter', '')), border=1, fill=fill)
                pdf.cell(30, 8, str(row.get('value', '')), border=1, fill=fill)
                pdf.cell(20, 8, str(row.get('unit', '')), border=1, fill=fill)
                pdf.cell(40, 8, status, border=1, fill=fill, new_x="LMARGIN", new_y="NEXT")
                fill = not fill

        pdf.output(pdf_path)
        return pdf_path

    def generate_csv(self, data: List[Dict[str, Any]], csv_path: str):
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    def preview_data(self, date_range: Dict[str, str], machine_id: str, shift: str, report_type: str) -> List[Dict[str, Any]]:
        res = self.fetch_data(date_range, machine_id, shift, report_type)
        return res["raw"]

    def generate_report(self, date_range: Dict[str, str], machine_id: str, shift: str, report_type: str, template_id: str, output_type: str = 'pdf', with_chart: bool = False) -> str:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        data_res = self.fetch_data(date_range, machine_id, shift, report_type)
        
        context = {
            "data": data_res["raw"], 
            "pivoted_data": data_res["pivoted"],
            "machine_id": machine_id, 
            "shift": shift, 
            "date_range": date_range, 
            "report_type": report_type
        }
        
        file_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if with_chart:
            chart_path = os.path.join(REPORTS_DIR, f"{file_id}_chart.png")
            self.generate_chart(data_res["raw"], chart_path)
        else:
            chart_path = None
            
        if output_type == 'pdf':
            pdf_path = os.path.join(REPORTS_DIR, f"{file_id}.pdf")
            self.generate_pdf(context, pdf_path, chart_path)
            return pdf_path
        else:
            csv_path = os.path.join(REPORTS_DIR, f"{file_id}.csv")
            self.generate_csv(data_res["raw"], csv_path)
            return csv_path
