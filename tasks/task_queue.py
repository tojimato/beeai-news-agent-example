# Standard library imports
import time
import asyncio

# Third-party imports
import redis

# Local imports
from src.config.professions import Profession
from src.config.settings import REDIS_URL
from src.utils.email_service import send_email
from src.pipelines.strategic_pipeline import StrategicPipeline, PipelineOutput
from src.report.report_generator import render_html_from_pipeline_output
from src.utils.logger import log_info, log_warning, log_error

REDIS_RATE_LIMIT_KEY: str = "last_email_sent_time"
RATE_LIMIT_SECONDS: int = 120

# Global Redis connection (reuse for all calls)
_redis_instance = redis.Redis.from_url(REDIS_URL)

def wait_for_rate_limit(redis_url: str = REDIS_URL) -> None:
    """
    Wait if the last email was sent less than RATE_LIMIT_SECONDS ago (distributed lock via Redis).

    Args:
        redis_url: Redis connection URL (default: REDIS_URL from settings).
    """
    lock_key = "last_email_lock"
    lock_ttl = 160  # seconds, lock auto-expires
    r = _redis_instance

    while not r.set(lock_key, "1", nx=True, ex=lock_ttl):
        log_warning("Another process holds the lock, waiting...")
        time.sleep(1)

    try:
        log_info(f"Rate limit function called with REDIS_URL: {redis_url}")
        last_sent = r.get(REDIS_RATE_LIMIT_KEY)
        now = int(time.time())

        # If no previous send, set and return
        if last_sent is None:
            r.set(REDIS_RATE_LIMIT_KEY, now)
            return

        last_sent = int(last_sent)
        elapsed = now - last_sent

        # If within rate limit, wait
        if elapsed < RATE_LIMIT_SECONDS:
            wait_time = RATE_LIMIT_SECONDS - elapsed
            log_warning(f"Rate limit enforced: waiting {wait_time} seconds before sending email.")
            time.sleep(wait_time)

        r.set(REDIS_RATE_LIMIT_KEY, int(time.time()))
    finally:
        r.delete(lock_key)

def _normalize_profession(profession: str | Profession) -> Profession | str:
    """
    Normalize a profession input to a Profession enum if possible, else return as string.

    Args:
        profession: Profession as string or Profession enum.

    Returns:
        Profession enum or original string if not matched.
    """
    if isinstance(profession, Profession):
        return profession

    if not isinstance(profession, str):
        log_warning(f"Invalid profession type: {type(profession)}. Using as string.")
        return str(profession)

    try:
        return Profession(profession.upper())
    except Exception:
        for p in Profession:
            if p.value == profession:
                return p
        log_warning(f"Unknown profession: {profession}, using as string.")
        return profession


def send_daily_report(email: str, profession: str | Profession, name: str) -> None:
    """
    Send a daily report email for a given profession and user.

    Args:
        email: Recipient email address.
        profession: Profession as string or Profession enum.
        name: Sender name for the email.
    """
    # Normalize profession
    normalized_profession = _normalize_profession(profession)

    log_info(f"Job triggered for {email}, {normalized_profession}, {name}")

    wait_for_rate_limit()

    log_info(f"Continuing to send report for {email}, {normalized_profession}, {name}")

    pipeline = StrategicPipeline(profession=normalized_profession)
    output: PipelineOutput = asyncio.run(pipeline.execute())

    body = render_html_from_pipeline_output(output, name)

    profession_str = (
        normalized_profession.value if hasattr(normalized_profession, 'value') else str(normalized_profession)
    )
    subject = f"Your Daily {profession_str.replace('_', ' ').title()} Report"

    send_email(email, subject, body, sender_name=name)