"""Simple, reliable logging for pipeline monitoring.

Logs token usage, costs, and errors. No complex side effects - just clean
file and console output. Error alerts handled separately via email_service.
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional, Tuple

from src.config.settings import LOG_FILE


class JsonFormatter(logging.Formatter):
    """Custom formatter to output all logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with proper escaping."""
        # Get message safely
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": message
        }

        if record.exc_info:
            import traceback
            log_entry["traceback"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        try:
            return json.dumps(log_entry, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Fallback if JSON encoding fails
            safe_message = str(message).replace('"', "'").replace("\n", "\\n")
            return json.dumps({
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": safe_message,
                "error": f"JSON encoding failed: {str(e)}"
            }, ensure_ascii=False)


def _setup_logging() -> None:
    """Initialize file logging with fallback to console on errors.

    Ensures log directory exists and file logging is configured.
    If file operations fail, falls back to console-only logging.
    Also configures APScheduler logs to use JSON format.
    """
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create file handler with JSON formatter
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(JsonFormatter())

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)

        # Configure APScheduler to reduce noise - only log INFO and above
        apscheduler_logger = logging.getLogger('apscheduler')
        apscheduler_logger.setLevel(logging.WARNING)  # Reduce APScheduler verbosity
        apscheduler_logger.handlers.clear()
        apscheduler_logger.propagate = True

    except (OSError, IOError) as e:
        # File logging failed, fallback to console
        print(f"⚠️  File logging disabled: {e}", file=sys.stderr)
        logging.basicConfig(level=logging.INFO, format='%(message)s')


_setup_logging()

def _extract_metrics(output: Any) -> Tuple[Optional[Any], Optional[Any]]:
    """Extract usage and cost metrics from BeeAI framework outputs.
    
    Supports both RequirementAgentOutput (with state) and ChatModelOutput
    (direct attributes) structures.
    
    Args:
        output: BeeAI framework output object (agent or model response).
    
    Returns:
        Tuple of (usage, cost) objects. Either may be None if not available.
    """
    # RequirementAgentOutput structure (contains state object)
    if hasattr(output, 'state'):
        usage = getattr(output.state, 'usage', None)
        cost = getattr(output.state, 'cost', None)
    # ChatModelOutput structure (direct attributes)
    else:
        usage = getattr(output, 'usage', None)
        cost = getattr(output, 'cost', None)
    
    return usage, cost

def log_token_usage(
    run_output: Any,
    task_name: str = "Task_Execution"
) -> dict[str, Any]:
    """Log token usage and costs from LLM execution.

    Args:
        run_output: BeeAI framework output (agent or model response).
        task_name: Identifier for this execution step.

    Returns:
        Dictionary with timestamp, tokens, and cost data.
    """
    usage, cost = _extract_metrics(run_output)

    prompt_tokens = getattr(usage, 'prompt_tokens', 0) if usage else 0
    completion_tokens = (
        getattr(usage, 'completion_tokens', 0) if usage else 0
    )
    total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
    cached_tokens = getattr(usage, 'cached_prompt_tokens', 0) if usage else 0
    total_cost_usd = getattr(cost, 'total_cost_usd', 0.0) if cost else 0.0

    log_data: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "task": task_name,
        "tokens": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
            "cached": cached_tokens
        },
        "cost_usd": total_cost_usd
    }

    # Print to console
    print(
        f"\n📊 [TOKEN & COST REPORT - {task_name}]\n"
        f"   Tokens: {total_tokens} (In: {prompt_tokens} | Out: "
        f"{completion_tokens} | Cached: {cached_tokens})\n"
        f"   Cost: ${total_cost_usd:.6f}"
    )

    # Log to file - use special marker for token usage data
    try:
        logger = logging.getLogger(__name__)
        # Format as readable string - JsonFormatter will wrap it
        log_msg = (
            f"[TOKEN_USAGE] {task_name} | "
            f"Tokens: {total_tokens} (prompt: {prompt_tokens}, "
            f"completion: {completion_tokens}, cached: {cached_tokens}) | "
            f"Cost: ${total_cost_usd:.6f}"
        )
        logger.info(log_msg)
    except Exception:
        # Fail silently - don't break the main pipeline
        pass

    return log_data

def summarize_total_usage(*run_outputs: Any) -> int:
    """Aggregate token usage across multiple LLM executions.

    Args:
        *run_outputs: Variable BeeAI framework output objects.

    Returns:
        Total token count across all outputs.
    """
    total_tokens = 0
    total_cost = 0.0

    print(
        "\n" + "═" * 55
        + f"\n📈 AGGREGATED USAGE SUMMARY\n"
        + "─" * 55
    )

    for i, output in enumerate(run_outputs, 1):
        usage, cost = _extract_metrics(output)
        if usage:
            step_tokens = getattr(usage, 'total_tokens', 0)
            step_cost = (
                getattr(cost, 'total_cost_usd', 0.0) if cost else 0.0
            )
            print(f"  Step {i}: {step_tokens:6} tokens | ${step_cost:.6f}")
            total_tokens += step_tokens
            total_cost += step_cost

    print(
        f"{'─' * 55}\n"
        f"  TOTAL: {total_tokens:6} tokens | ${total_cost:.6f}\n"
        + "═" * 55 + "\n"
    )

    return total_tokens

def log_info(message: str) -> None:
    """Log info message to console and file (JSON format)."""
    print(message)
    _write_json_log("INFO", message)


def log_warning(message: str) -> None:
    """Log warning message to console and file (JSON format)."""
    print(f"⚠️  {message}")
    _write_json_log("WARNING", message)


def log_error(message: str, exc_info: bool = False) -> None:
    """Log error message to console and file (JSON format)."""
    print(f"❌ {message}")
    _write_json_log("ERROR", message, exc_info=exc_info)


def log_debug(message: str) -> None:
    """Log debug message to console and file (JSON format)."""
    print(f"🔍 {message}")
    _write_json_log("DEBUG", message)


def log_exception(message: str) -> None:
    """Log exception with full traceback (JSON format)."""
    print(f"💥 {message}")
    _write_json_log("EXCEPTION", message, exc_info=True)


def _write_json_log(level: str, message: str, exc_info: bool = False) -> None:
    """Write structured JSON log entry to file with correct level.

    Args:
        level: Log level (INFO, WARNING, ERROR, DEBUG, EXCEPTION).
        message: Log message.
        exc_info: Include traceback if True.
    """
    try:
        # Use logging directly - JsonFormatter will handle JSON conversion
        logger = logging.getLogger(__name__)

        # Use correct logging level - pass exc_info to logger so formatter
        # can extract traceback into separate field
        if level == "DEBUG":
            logger.debug(message, exc_info=exc_info)
        elif level == "INFO":
            logger.info(message, exc_info=exc_info)
        elif level == "WARNING":
            logger.warning(message, exc_info=exc_info)
        elif level == "ERROR":
            logger.error(message, exc_info=exc_info)
        elif level == "EXCEPTION":
            logger.exception(message)
        else:
            logger.info(message, exc_info=exc_info)
    except Exception:
        # Fail silently - don't break the main pipeline
        pass
