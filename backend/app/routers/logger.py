from fastapi import APIRouter, HTTPException, Body, Query
import logging
import os
import json
from fastapi.responses import FileResponse
from typing import Optional
from app.services.logger_service import EventLogger

router = APIRouter(tags=["logger"], prefix="/logger")
event_logger = EventLogger()

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
LOG_FILE = os.path.join(LOGS_DIR, 'activity.log')

os.makedirs(LOGS_DIR, exist_ok=True)

# Activity entries are written directly to LOG_FILE below; logging config is
# owned centrally by app.main (do not call basicConfig here — it conflicts).
logger = logging.getLogger(__name__)

MAX_LOG_ENTRY_BYTES = 16 * 1024  # cap a single entry to prevent disk abuse

@router.post("/log")
def write_log(entry: dict = Body(...)):
    # Accepts structured log entries (a JSON object).
    serialized = json.dumps(entry, default=str)
    if len(serialized.encode("utf-8")) > MAX_LOG_ENTRY_BYTES:
        raise HTTPException(status_code=413, detail="Log entry too large")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(serialized + "\n")
    except OSError:
        logging.exception("Failed to write log entry")
        raise HTTPException(status_code=500, detail="Failed to write log entry")
    return {"message": "Log entry added."}

@router.get("/")
def get_logs(limit: int = Query(100, ge=1, le=1000)):
    # Return the last N log entries, skipping any corrupt lines.
    if not os.path.exists(LOG_FILE):
        return {"logs": []}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
    except OSError:
        logging.exception("Failed to read log file")
        raise HTTPException(status_code=500, detail="Failed to read logs")
    logs = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"logs": logs}

@router.get("/download")
def download_log():
    if not os.path.exists(LOG_FILE):
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(LOG_FILE, filename="activity.log")

@router.get("/activity")
def get_activity_logs(limit: Optional[int] = Query(100)):
    logs = event_logger.get_logs(limit=limit)
    return {"logs": logs}
