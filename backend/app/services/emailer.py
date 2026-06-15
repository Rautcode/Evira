import smtplib
from email.message import EmailMessage
import os
from typing import Optional
import logging

def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    receiver: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None
) -> bool:
    """
    Send an email with optional attachment. Logs success/failure.
    Supports Gmail/Outlook SMTP.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = receiver
    msg.set_content(body)

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
            maintype, subtype = ("application", "octet-stream")
            if file_name.endswith(".pdf"):
                maintype, subtype = ("application", "pdf")
            elif file_name.endswith(".csv"):
                maintype, subtype = ("text", "csv")
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logging.info(f"Email sent to {receiver} with subject '{subject}'")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {receiver}: {e}")
        return False
