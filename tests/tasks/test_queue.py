import pytest
from src.config.professions import Profession
from src.config.settings import SMTP_USER, SMTP_PASS, ALERT_EMAIL
from tasks.task_queue import send_daily_report


@pytest.mark.skipif(
    not (SMTP_USER and SMTP_PASS),
    reason="SMTP credentials not set in settings."
)
def test_send_daily_report_runs():
    # This will run the full pipeline and send a real email. Use test credentials!
    test_email = ALERT_EMAIL
    profession = Profession.SOLO_DEVELOPER
    name = 'Test User'

    try:
        send_daily_report(test_email, profession, name)
    except Exception as e:
        pytest.fail(f"send_daily_report failed: {e}")
