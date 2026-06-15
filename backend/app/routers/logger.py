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

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

@router.post("/log")
def write_log(entry: dict = Body(...)):
    # Accepts structured log entries
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + "\n")
    return {"message": "Log entry added."}

@router.get("/")
def get_logs(limit: Optional[int] = 100):
    # Return the last N log entries
    if not os.path.exists(LOG_FILE):
        return {"logs": []}
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()[-limit:]
        logs = [json.loads(line) for line in lines]
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
