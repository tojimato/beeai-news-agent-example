import pytest
from src.config.settings import ALERT_EMAIL, SMTP_USER, SMTP_PASS
from src.utils.email_service import send_email


@pytest.mark.skipif(
    not (SMTP_USER and SMTP_PASS),
    reason="SMTP credentials not set in settings."
)
def test_send_report_email():
    # This test will actually send an email. Use a test account!
    subject = "Test Email"
    body = "This is a test report email."
    try:
        send_email(ALERT_EMAIL, subject, body, sender_name="BeeAgent")
    except Exception as e:
        pytest.fail(f"Email sending failed: {e}")
