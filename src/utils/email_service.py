import smtplib
from email.message import EmailMessage
from src.config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

def send_email(email: str, subject: str, body: str, sender_name: str = None) -> None:
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{sender_name or SMTP_USER} <{SMTP_USER}>"
    msg['To'] = email
    msg.set_content(body, subtype='html')

    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
