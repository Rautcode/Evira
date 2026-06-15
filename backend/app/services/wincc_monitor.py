import os
import csv
from datetime import datetime
from typing import Optional

LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs/wincc_activity.csv'))
LOGS_DIR = os.path.dirname(LOG_FILE)

class WinCCActivityLogger:
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or LOG_FILE
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "user", "details"])
                writer.writeheader()

    def log(self, event: str, user: str, details: str = ""):
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "user", "details"])
            writer.writerow({
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "user": user,
                "details": details
            })

# Example usage:
# logger = WinCCActivityLogger()
# logger.log("login", "jane.doe", "User logged in")
# logger.log("report_gen", "jane.doe", "Generated daily report")
