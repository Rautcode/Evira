from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.emailer import send_email
from typing import Optional, List
import logging

router = APIRouter(tags=["email"], prefix="/email")

from app.services.email_service import email_service

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

@router.put("/settings")
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
    def send_and_log():
        recipients = [r.strip() for r in data.to.split(",") if r.strip()]
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
