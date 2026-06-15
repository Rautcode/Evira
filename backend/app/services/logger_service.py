import os
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

LOGS_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/events.csv'))
LOGS_DIR = os.path.dirname(LOGS_CSV)

class EventLogger:
    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or LOGS_CSV
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "user", "details"])
                writer.writeheader()

    def log_event(self, event: str, user: str, details: str = ""):
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "user", "details"])
            writer.writerow({
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "user": user,
                "details": details
            })

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        df = pd.read_csv(self.csv_path)
        return df.tail(limit).to_dict(orient='records')

    def generate_summary(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        summary = df.groupby('event').size().reset_index(name='count')
        return summary

    def export_summary_csv(self, out_path: str) -> str:
        summary = self.generate_summary()
        summary.to_csv(out_path, index=False)
        return out_path

    def export_summary_pdf(self, out_path: str) -> str:
        summary = self.generate_summary()
        c = canvas.Canvas(out_path, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 14)
        c.drawString(40, height - 40, "Event Log Summary Report")
        c.setFont("Helvetica", 10)
        y = height - 80
        for _, row in summary.iterrows():
            c.drawString(60, y, f"{row['event']}: {row['count']}")
            y -= 20
        c.save()
        return out_path

    def plot_event_counts(self, out_path: str) -> str:
        summary = self.generate_summary()
        plt.figure(figsize=(8,4))
        plt.bar(summary['event'], summary['count'], color='skyblue')
        plt.title('Event Counts')
        plt.xlabel('Event')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        return out_path
