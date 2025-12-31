import smtplib
from email.message import EmailMessage
from email.header import Header
from src.config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

def send_email(email: str, subject: str, body: str, sender_name: str = None) -> None:
    # Ensure UTF-8 encoding for all headers and body, set all headers as plain str
    msg = EmailMessage()
    msg['Subject'] = str(subject)
    if sender_name:
        msg['From'] = f"{str(sender_name)} <{SMTP_USER}>"
    else:
        msg['From'] = SMTP_USER
    msg['To'] = email
    msg.set_content(str(body), subtype='html')

    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
