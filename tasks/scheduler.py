import json
import time
from apscheduler.schedulers.background import BackgroundScheduler

from tasks.task_queue import send_daily_report
from src.utils.logger import log_info


def run_scheduler() -> None:
    """
    Schedule daily report jobs for each recipient at specified hour/minute.
    Reads recipients from recipients.json and schedules jobs using APScheduler.
    """
    with open('recipients.json', encoding='utf-8') as f:
        recipients = json.load(f)

    scheduler = BackgroundScheduler()

    for idx, rec in enumerate(recipients):
        scheduler.add_job(
            send_daily_report,
            'cron',
            hour=rec['hour'],
            minute=rec['minute'],
            args=(rec['email'], rec['profession'], rec['name'], rec.get('language', 'tr')),
            id=f'send-report-{idx}'
        )

    scheduler.start()
    log_info('APScheduler started. Press Ctrl+C to exit.')

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    run_scheduler()