import os
import pytest
from src.config.professions import Profession
from tasks.task_queue import send_daily_report

@pytest.mark.skipif(
    not (os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASS')),
    reason="SMTP credentials not set in environment."
)
def test_send_daily_report_runs():
    # This will run the full pipeline and send a real email. Use test credentials!
    test_email = "tojimato@gmail.com"
    profession =  Profession.SOLO_DEVELOPER
    name = 'Test User'
    
    try:
        send_daily_report(test_email, profession, name)
    except Exception as e:
        pytest.fail(f"send_daily_report failed: {e}")
