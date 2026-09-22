import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def notify_new_enquiry(enquiry: dict) -> bool:
    """Send an optional notification after an enquiry has been committed."""
    host = os.getenv("SMTP_HOST", "").strip()
    port_value = os.getenv("SMTP_PORT", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip()
    recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL", "").strip()

    if not all((host, port_value, sender, recipient)):
        logger.warning("Email notification is not configured; enquiry was saved without sending email.")
        return False

    try:
        port = int(port_value)
        message = EmailMessage()
        message["Subject"] = "New Admission Enquiry — Jigisha International School"
        message["From"] = sender
        message["To"] = recipient
        message.set_content(
            "New admission enquiry received.\n\n"
            f"Parent: {enquiry['parent']}\n"
            f"Student: {enquiry['student']}\n"
            f"Email: {enquiry['email']}\n"
            f"Mobile: {enquiry['mobile']}\n"
            f"Grade: {enquiry['grade']}\n"
            f"Message: {enquiry['message']}\n"
            f"Submitted at: {enquiry['created_at']}\n"
        )

        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=15) as smtp:
                if username:
                    smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                if username:
                    smtp.login(username, password)
                smtp.send_message(message)
        logger.info("Email notification sent for enquiry %s.", enquiry.get("id", ""))
        return True
    except Exception:
        logger.exception("Email notification failed for enquiry %s; enquiry remains saved.", enquiry.get("id", ""))
        return False
