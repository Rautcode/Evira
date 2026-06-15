from fastapi import APIRouter, Body, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import logging
import os
from datetime import datetime, timedelta
from app.services.report_service import ReportService
from app.services.emailer import send_email

# Set up SQLite job store
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{os.path.join(DB_DIR, "jobs.sqlite")}')
}

router = APIRouter(tags=["scheduler"], prefix="/scheduler")
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
LOG_FILE = os.path.join(LOGS_DIR, 'scheduler.log')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

class ScheduleRequest(BaseModel):
    title: str
    template_id: str
    machine_id: str
    cron_expression: str
    report_type: str = 'pdf'
    recipients: str = ''

def job_wrapper(job_id, title, template_id, machine_id, report_type, recipients):
    try:
        logging.info(f"[Job {job_id}] Starting report generation: {title}")
        report_service = ReportService()
        
        # Determine dynamic date range (e.g. yesterday to today)
        date_range = {
            "start": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), 
            "end": datetime.now().strftime("%Y-%m-%d")
        }
        
        file_path = report_service.generate_report(
            date_range=date_range,
            machine_id=machine_id,
            shift='Full',
            report_type='scheduled',
            template_id=template_id,
            output_type=report_type,
            with_chart=True
        )
        logging.info(f"[Job {job_id}] Report generated: {file_path}")
        
        if recipients:
            email_service = None
            try:
                from app.services.email_service import email_service
            except ImportError:
                pass
                
            if email_service:
                recipients_list = [r.strip() for r in recipients.split(",") if r.strip()]
                for to_email in recipients_list:
                    email_service.send_email(
                        subject=f"Scheduled SCADA Report: {title}",
                        body=f"Please find the attached automated report: {title}.",
                        to_email=to_email,
                        attachment_path=file_path
                    )
                logging.info(f"[Job {job_id}] Emails dispatched.")
        logging.info(f"[Job {job_id}] Job completed successfully.")
    except Exception as e:
        logging.error(f"[Job {job_id}] Job failed: {e}")

@router.get("")
@router.get("/")
def list_jobs():
    jobs = []
    for job in scheduler.get_jobs():
        args = job.args
        jobs.append({
            "id": job.id,
            "title": job.name,
            "status": "active",
            "template_id": args[2] if len(args) > 2 else "Unknown",
            "cron_expression": str(job.trigger),
            "nextRun": str(job.next_run_time) if job.next_run_time else None
        })
    return jobs

@router.post("")
@router.post("/")
def add_job(data: ScheduleRequest = Body(...)):
    job_id = str(uuid.uuid4())
    try:
        trigger = CronTrigger.from_crontab(data.cron_expression)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cron expression: '{data.cron_expression}'",
        )

    args = [job_id, data.title, data.template_id, data.machine_id, data.report_type, data.recipients]
    
    scheduler.add_job(
        job_wrapper, 
        trigger, 
        args=args, 
        id=job_id, 
        name=data.title, 
        replace_existing=True
    )
    logging.info(f"[Job {job_id}] Scheduled with cron '{data.cron_expression}'")
    return {"message": "Job added", "job_id": job_id}

@router.delete("/{job_id}")
def remove_job(job_id: str):
    if not scheduler.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        scheduler.remove_job(job_id)
    except Exception:
        logging.exception(f"[Job {job_id}] Failed to remove")
        raise HTTPException(status_code=500, detail="Failed to remove job")
    logging.info(f"[Job {job_id}] Removed")
    return {"message": "Job removed"}
