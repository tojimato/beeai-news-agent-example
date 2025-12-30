import pytest
from src.report.email_service import send_report_email
import os

@pytest.mark.skipif(
    not (os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASS')),
    reason="SMTP credentials not set in environment."
)
def test_send_report_email():
    # This test will actually send an email. Use a test account!
    test_email = "tojimato@gmail.com"
    test_name = "Test User"
    test_report = "This is a test report email."
    try:
        send_report_email(test_email, test_name, test_report)
    except Exception as e:
        pytest.fail(f"Email sending failed: {e}")
