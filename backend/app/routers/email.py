from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Depends
from app.core.security import require_role
from pydantic import BaseModel
from typing import Optional
import logging
import os

from email_validator import validate_email, EmailNotValidError
from app.utils.safe_paths import is_within_any

router = APIRouter(tags=["email"], prefix="/email")

from app.services.email_service import email_service

# Attachments may only come from the app's own generated-output directories,
# never arbitrary paths on disk (prevents exfiltration of e.g. /etc/passwd).
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ALLOWED_ATTACHMENT_DIRS = [
    os.path.join(_BACKEND_ROOT, "reports"),
    os.path.join(_BACKEND_ROOT, "charts"),
    os.path.join(_BACKEND_ROOT, "outputs"),
]

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    attachment_path: Optional[str] = None

class SmtpSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str

@router.get("/settings")
def get_settings():
    email_service.load_config()
    return {
        "host": email_service.smtp_host,
        "port": email_service.smtp_port,
        "user": email_service.smtp_user,
        "password": ""  # Never return the password
    }

@router.put("/settings", dependencies=[Depends(require_role("engineer"))])
def update_settings(data: SmtpSettings = Body(...)):
    email_service.save_config(
        host=data.host,
        port=data.port,
        user=data.user,
        password=data.password
    )
    return {"success": True, "message": "SMTP settings updated securely."}

@router.post("/send")
def send_email_route(
    data: EmailRequest = Body(...),
    background_tasks: BackgroundTasks = None
):
    # Validate recipients up front so the caller gets a real error, not a
    # silent background failure.
    raw_recipients = [r.strip() for r in data.to.split(",") if r.strip()]
    if not raw_recipients:
        raise HTTPException(status_code=400, detail="At least one recipient is required")
    recipients = []
    for r in raw_recipients:
        try:
            recipients.append(validate_email(r, check_deliverability=False).normalized)
        except EmailNotValidError:
            raise HTTPException(status_code=400, detail=f"Invalid email address: {r}")

    # An attachment, if provided, must live inside an allowed output directory.
    if data.attachment_path:
        if not os.path.isfile(data.attachment_path) or not is_within_any(
            data.attachment_path, ALLOWED_ATTACHMENT_DIRS
        ):
            raise HTTPException(status_code=400, detail="Invalid or disallowed attachment path")

    def send_and_log():
        for recipient in recipients:
            result = email_service.send_email(
                subject=data.subject,
                body=data.body,
                to_email=recipient,
                attachment_path=data.attachment_path
            )
            if result:
                logging.info(f"Email sent to {recipient} with subject '{data.subject}'")
            else:
                logging.error(f"Failed to send email to {recipient} with subject '{data.subject}'")
                
    if background_tasks:
        background_tasks.add_task(send_and_log)
    else:
        send_and_log()
    return {"success": True, "message": "Email is being sent in the background."}
