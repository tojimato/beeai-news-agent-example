"""Send error alerts via email without triggering logger recursion.

Decoupled from logger to prevent circular dependencies and recursion.
Call this directly from critical error handlers (Redis, scheduler, etc).
"""
import os
from src.utils.email_service import send_email


def send_error_alert(error_type: str, message: str, details: str = "") -> None:
    """Send error alert email if ALERT_EMAIL configured.

    Args:
        error_type: Type of error (e.g. "Redis Error", "Scheduler Error").
        message: Brief error message (will be email subject).
        details: Optional detailed error information (will be email body).
    """
    alert_email = os.environ.get("ALERT_EMAIL")
    if not alert_email:
        # No alert email configured, skip
        return

    try:
        subject = f"[BeeAI] {error_type}: {message[:50]}"
        body = f"<b>Error:</b> {message}<br>" + (
            f"<b>Details:</b><pre>{details}</pre>"
            if details else ""
        )
        send_email(
            email=alert_email,
            subject=subject,
            body=body,
            sender_name="BeeAI Alert Service"
        )
    except Exception as e:
        # Fail silently - don't let email errors break the app
        import sys
        print(f"⚠️  Alert email failed: {e}", file=sys.stderr)
