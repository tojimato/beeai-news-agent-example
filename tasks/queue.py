from celery import Celery
from src.report.email_service import send_report_email
from src.core.report_generator import generate_report_for_profession

app = Celery('beeai', broker='redis://localhost:6379/0')

@app.task
def send_daily_report(email: str, profession: str, name: str):
    report = generate_report_for_profession(profession)
    send_report_email(email, name, report)
