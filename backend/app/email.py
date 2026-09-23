import logging
import os

import resend

logger = logging.getLogger(__name__)

EMAIL_SUBJECT = "New Admission Enquiry — Jigisha International School"
REVIEW_EMAIL_SUBJECT = "New Review Submitted — Jigisha International School"


def notify_new_enquiry(enquiry: dict) -> bool:
    """Send a Resend notification after an enquiry has been committed."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL", "").strip()

    if not api_key or not sender or not recipient:
        logger.warning("Email notification is not configured; enquiry was saved without sending email.")
        return False

    body = (
        "New admission enquiry received.\n\n"
        f"Parent: {enquiry['parent']}\n"
        f"Student: {enquiry['student']}\n"
        f"Email: {enquiry['email']}\n"
        f"Mobile: {enquiry['mobile']}\n"
        f"Grade: {enquiry['grade']}\n"
        f"Message: {enquiry['message']}\n"
        f"Submitted at: {enquiry['created_at']}\n"
    )

    try:
        resend.api_key = api_key
        response = resend.Emails.send(
            {
                "from": sender,
                "to": [recipient],
                "subject": EMAIL_SUBJECT,
                "text": body,
            }
        )
        if not response:
            logger.error("Resend did not accept the email for enquiry %s; enquiry remains saved.", enquiry.get("id", ""))
            return False
        logger.info("Email notification accepted by Resend for enquiry %s.", enquiry.get("id", ""))
        return True
    except Exception:
        # Do not log the exception text: SDK errors can contain request details.
        logger.error(
            "Email notification failed for enquiry %s; enquiry remains saved.",
            enquiry.get("id", ""),
        )
        return False


def notify_new_review(review: dict) -> bool:
    """Send an approval reminder after a review has been committed."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL", "").strip()

    if not api_key or not sender or not recipient:
        logger.warning("Email notification is not configured; review was saved without sending email.")
        return False

    body = (
        "A new review has been submitted and is awaiting admin approval.\n\n"
        f"Name: {review['name']}\n"
        f"Role: {review['role']}\n"
        f"Rating: {review['rating']} / 5\n"
        f"Review: {review['review']}\n"
        f"Submitted at: {review['created_at']}\n\n"
        "Please review it in the Jigisha administration dashboard."
    )

    try:
        resend.api_key = api_key
        response = resend.Emails.send({"from": sender, "to": [recipient], "subject": REVIEW_EMAIL_SUBJECT, "text": body})
        if not response:
            logger.error("Resend did not accept the email for review %s; review remains pending.", review.get("id", ""))
            return False
        logger.info("Review notification accepted by Resend for review %s.", review.get("id", ""))
        return True
    except Exception:
        logger.error("Email notification failed for review %s; review remains pending.", review.get("id", ""))
        return False
