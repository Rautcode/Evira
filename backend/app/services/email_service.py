"""Email service."""

import os
import json
import logging
from app.services.emailer import send_email
from app.utils.config_manager import config_manager
from app.utils.db import add_activity_log

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.load_config()

    def load_config(self):
        config = config_manager.load_config()
        email_config = config.get("email", {})
        self.smtp_host = email_config.get("smtp_host", os.getenv("SMTP_HOST", "smtp.gmail.com"))
        self.smtp_port = email_config.get("smtp_port", int(os.getenv("SMTP_PORT", 587)))
        self.smtp_user = email_config.get("smtp_user", os.getenv("SMTP_USER", ""))
        self.smtp_pass = email_config.get("smtp_pass", os.getenv("SMTP_PASS", ""))

    def save_config(self, host: str, port: int, user: str, password: str):
        self.smtp_host = host
        self.smtp_port = port
        self.smtp_user = user
        self.smtp_pass = password
        
        config = config_manager.load_config()
        config["email"] = {
            "smtp_host": host,
            "smtp_port": port,
            "smtp_user": user,
            "smtp_pass": password
        }
        config_manager.save_config(config)

    def check_connection(self) -> bool:
        """Check if the email service connection is configured."""
        self.load_config()
        if self.smtp_host and self.smtp_port and self.smtp_user and self.smtp_pass:
            logger.info("Email service connection parameters are configured.")
            return True
        else:
            logger.warning("Email service connection parameters are not fully configured.")
            return False

    def send_email(
        self,
        subject: str,
        body: str,
        to_email: str,
        attachment_path: str = None
    ) -> bool:
        """Send an email using the configured emailer."""
        self.load_config()
        
        if not self.smtp_host or not self.smtp_user or not self.smtp_pass:
            logger.error("Email service connection parameters are not fully configured.")
            return False
            
        logger.info(f"Attempting to send email to {to_email} with subject '{subject}'")
        success = send_email(
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            smtp_user=self.smtp_user,
            smtp_pass=self.smtp_pass,
            receiver=to_email,
            subject=subject,
            body=body,
            attachment_path=attachment_path
        )
        if success:
            logger.info(f"Email sent successfully to {to_email}")
            add_activity_log(
                event_type="email_success",
                description=f"Automated email '{subject}' sent to {to_email}.",
                severity="info",
                source="EmailService"
            )
        else:
            logger.error(f"Failed to send email to {to_email}")
            add_activity_log(
                event_type="email_failure",
                description=f"Failed to send automated email to {to_email}.",
                severity="error",
                source="EmailService"
            )
        return success

email_service = EmailService()
