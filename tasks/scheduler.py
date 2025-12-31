import json
import time
from apscheduler.schedulers.background import BackgroundScheduler

from tasks.task_queue import send_daily_report
from src.utils.logger import log_info, log_error


def _load_recipients() -> list[dict]:
    """Load recipients from recipients.json with error handling.
    
    Returns:
        List of recipient dictionaries.
    
    Raises:
        RuntimeError: If file not found or JSON is invalid.
    """
    try:
        with open('recipients.json', encoding='utf-8') as f:
            recipients = json.load(f)
        
        if not isinstance(recipients, list):
            raise ValueError("recipients.json must contain a JSON array.")
        
        log_info(f"Loaded {len(recipients)} recipients from recipients.json")
        return recipients
    except FileNotFoundError as e:
        raise RuntimeError("recipients.json not found.") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in recipients.json: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Error loading recipients: {str(e)}") from e


def run_scheduler() -> None:
    """Schedule daily report jobs for each recipient at specified hour/minute.
    
    Reads recipients from recipients.json and schedules jobs using APScheduler.
    Each recipient must have: email, profession, name, hour, minute, language (optional).
    """
    try:
        recipients = _load_recipients()
    except RuntimeError as e:
        log_error(f"Failed to load recipients: {str(e)}")
        return

    scheduler = BackgroundScheduler()

    for idx, rec in enumerate(recipients):
        try:
            # Validate required fields
            required_fields = ['email', 'profession', 'name', 'hour', 'minute']
            missing = [f for f in required_fields if f not in rec]
            if missing:
                log_error(
                    f"Recipient {idx}: missing fields {missing}. Skipping."
                )
                continue

            # Schedule job
            scheduler.add_job(
                send_daily_report,
                'cron',
                hour=rec['hour'],
                minute=rec['minute'],
                args=(
                    rec['email'],
                    rec['profession'],
                    rec['name'],
                    rec.get('language', 'tr')
                ),
                id=f'send-report-{idx}',
                replace_existing=True
            )
            log_info(
                f"Scheduled: {rec['email']} at {rec['hour']:02d}:{rec['minute']:02d}"
            )
        except Exception as e:
            log_error(f"Failed to schedule recipient {idx}: {str(e)}")

    try:
        scheduler.start()
        log_info('APScheduler started. Press Ctrl+C to exit.')

        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log_info("APScheduler shutdown complete.")
    except Exception as e:
        log_error(f"Scheduler error: {str(e)}")
        scheduler.shutdown()