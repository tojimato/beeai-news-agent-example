import pytest
from src.utils.email_service import send_email
import os

@pytest.mark.skipif(
    not (os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASS')),
    reason="SMTP credentials not set in environment."
)
def test_send_report_email():
    # This test will actually send an email. Use a test account!
    test_email = os.environ.get('SMTP_USER')
    subject = "Test Email"
    body = "This is a test report email."
    try:
        send_email(test_email, subject, body, sender_name="Test User")
    except Exception as e:
        pytest.fail(f"Email sending failed: {e}")
