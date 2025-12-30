import json
from celery.schedules import crontab
from tasks.queue import app, send_daily_report

with open('recipients.json') as f:
    recipients = json.load(f)

for idx, rec in enumerate(recipients):
    app.conf.beat_schedule[f'send-report-{idx}'] = {
        'task': 'tasks.queue.send_daily_report',
        'schedule': crontab(hour=rec['hour'], minute=rec['minute']),
        'args': (rec['email'], rec['profession'], rec['name']),
    }
