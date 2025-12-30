
import smtplib
from email.message import EmailMessage
from src.config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

def send_report_email(email: str, name: str, report: str) -> None:
    msg = EmailMessage()
    msg['Subject'] = 'Your Daily Report'
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg.set_content(f"Hi {name},\n\n{report}")

    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
