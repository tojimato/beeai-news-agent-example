# Standard library imports
import time
import asyncio

# Third-party imports
import redis
from pydantic import ValidationError

# Local imports
from src.config.professions import Profession
from src.config.validation import PipelineInputModel
from src.core.redis_client import RedisClient
from src.utils.email_service import send_email
from src.pipelines.strategic_pipeline import StrategicPipeline, PipelineOutput
from src.report.report_generator import render_html_from_pipeline_output
from src.utils.logger import log_info, log_warning, log_error
from src.utils.retry import retry_with_backoff

REDIS_RATE_LIMIT_KEY: str = "last_email_sent_time"
RATE_LIMIT_SECONDS: int = 120
LOCK_KEY: str = "last_email_lock"
LOCK_TTL: int = 160

def wait_for_rate_limit() -> None:
    """Wait if last email was sent within RATE_LIMIT_SECONDS (distributed lock via Redis).

    Uses Redis connection pool for thread-safe concurrent access with
    automatic timeout and health checks.

    Raises:
        RuntimeError: If Redis connection fails.
    """
    try:
        r = RedisClient.get_instance()
    except redis.ConnectionError as e:
        log_error(f"Redis unavailable: {str(e)}")
        raise RuntimeError(f"Rate limit service unavailable: {str(e)}") from e

    # Acquire distributed lock
    lock_acquired = False
    retries = 0
    max_retries = 5

    while retries < max_retries:
        try:
            if r.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL):
                lock_acquired = True
                break
        except redis.ConnectionError as e:
            log_error(f"Redis lock error (retry {retries+1}): {str(e)}")
            retries += 1
            time.sleep(1)
            continue

        log_warning("Another process holds the lock, waiting...")
        time.sleep(1)
        retries += 1

    if not lock_acquired:
        raise RuntimeError("Failed to acquire rate limit lock after retries")

    try:
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
            log_warning(
                f"Rate limit enforced: waiting {wait_time}s before next email."
            )
            time.sleep(wait_time)

        r.set(REDIS_RATE_LIMIT_KEY, int(time.time()))

    except redis.ConnectionError as e:
        log_error(f"Redis connection failed in rate limit check: {str(e)}")
        raise RuntimeError(f"Rate limit check failed: {str(e)}") from e
    finally:
        try:
            r.delete(LOCK_KEY)
        except redis.ConnectionError:
            log_warning("Failed to release lock, will expire in 160s")

def _normalize_profession(profession: str | Profession) -> Profession | str:
    """Normalize profession input to Profession enum if possible.
    
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


def _format_profession_name(profession: Profession | str) -> str:
    """Format profession enum/string as human-readable title.
    
    Args:
        profession: Profession enum or string value.
    
    Returns:
        Formatted profession name for display.
    """
    prof_str = (
        profession.value
        if hasattr(profession, 'value')
        else str(profession)
    )
    return prof_str.replace('_', ' ').title()


@retry_with_backoff(max_retries=2, initial_wait=2.0)
def _execute_pipeline_with_retry(
    profession: Profession | str,
    language: str
) -> PipelineOutput:
    """Execute pipeline with automatic retry on failure.
    
    Args:
        profession: Profession for pipeline.
        language: Language code for pipeline.
    
    Returns:
        PipelineOutput from successful execution.
    
    Raises:
        RuntimeError: If pipeline execution fails after retries.
    """
    try:
        # Validate pipeline inputs
        try:
            PipelineInputModel(profession=str(profession), language=language)
        except ValidationError as e:
            error_details = ", ".join(
                f"{err['loc'][0]}: {err['msg']}" for err in e.errors()
            )
            raise ValueError(f"Invalid pipeline inputs: {error_details}") from e
        
        pipeline = StrategicPipeline(profession=profession, language=language)
        output: PipelineOutput = asyncio.run(pipeline.execute())
        return output
    except Exception as e:
        raise RuntimeError(
            f"Pipeline execution failed: {type(e).__name__}: {str(e)}"
        ) from e


def send_daily_report(
    email: str,
    profession: str | Profession,
    name: str,
    language: str = "tr"
) -> None:
    """Send daily report email with full error handling and retry logic.
    
    Args:
        email: Recipient email address.
        profession: Profession as string or Profession enum.
        name: Recipient name for personalization.
        language: Language code ("tr" or "en").
    
    Logs detailed error info if pipeline or email send fails; does not re-raise.
    """
    try:
        # Normalize profession
        normalized_profession = _normalize_profession(profession)
        log_info(
            f"Job triggered: {email} | {normalized_profession} | {name} | {language}"
        )

        # Check rate limit
        try:
            wait_for_rate_limit()
        except RuntimeError as e:
            log_error(
                f"Rate limit check failed for {email}: {str(e)}. Aborting send."
            )
            return

        # Execute pipeline with retry
        output: PipelineOutput = _execute_pipeline_with_retry(
            normalized_profession,
            language
        )

        # Render email body
        body = render_html_from_pipeline_output(output, name, language=language)

        # Format subject
        profession_str = _format_profession_name(normalized_profession)
        subject = f"Your Daily {profession_str} Report"

        # Send email
        send_email(email, subject, body, sender_name=name)
        log_info(f"Report sent successfully to {email}")

    except Exception as e:
        log_error(
            f"Failed to send report for {email}: {type(e).__name__}: {str(e)}"
        )