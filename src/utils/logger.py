"""Token and cost tracking utilities for LLM pipeline monitoring.

This module provides functions to extract usage metrics (tokens, cost) from
BeeAI framework outputs and log them in a structured format for observability.
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional, Tuple

from src.config.settings import LOG_FILE
from src.utils.email_service import send_email

# Configure file-based logging for usage metrics
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

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

def log_token_usage(run_output: Any, task_name: str = "Task_Execution") -> dict[str, Any]:
    """Log token usage and cost metrics from an LLM execution.
    
    Extracts usage metrics from the output, prints a formatted console report,
    and logs structured JSON to the usage log file.
    
    Args:
        run_output: BeeAI framework output (agent or model response).
        task_name: Human-readable identifier for this execution step.
    
    Returns:
        Dictionary containing structured log data (timestamp, tokens, cost).
    """
    usage, cost = _extract_metrics(run_output)
    
    # Safely extract token counts (default to 0 if unavailable)
    prompt_tokens = getattr(usage, 'prompt_tokens', 0) if usage else 0
    completion_tokens = getattr(usage, 'completion_tokens', 0) if usage else 0
    total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
    cached_tokens = getattr(usage, 'cached_prompt_tokens', 0) if usage else 0
    
    # Safely extract cost data
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
    
    # Print formatted console summary
    success_indicator = "✅ Success" if total_tokens > 0 else "⚠️ No data"
    print(
        f"\n📊 [TOKEN & COST REPORT - {task_name}]\n"
        f"   Tokens: {total_tokens} (In: {prompt_tokens} | Out: {completion_tokens} | Cached: {cached_tokens})\n"
        f"   Cost: ${total_cost_usd:.6f}\n"
        f"   Status: {success_indicator}"
    )
    
    # Persist to log file
    logging.info(json.dumps(log_data))
    
    return log_data

def summarize_total_usage(*run_outputs: Any) -> int:
    """Aggregate and summarize token usage across multiple LLM executions.
    
    Prints a formatted table showing token counts and costs for each step,
    followed by totals. Helpful for understanding cost distribution across
    a multi-stage pipeline.
    
    Args:
        *run_outputs: Variable number of BeeAI framework output objects.
    
    Returns:
        Total token count across all outputs.
    """
    total_tokens = 0
    total_cost = 0.0
    
    print(
        "\n" + "═" * 55
        + f"\n📈 AGGREGATED USAGE SUMMARY | {datetime.now().strftime('%H:%M:%S')}\n"
        + "─" * 55
    )

    for i, output in enumerate(run_outputs, 1):
        usage, cost = _extract_metrics(output)

        if usage:
            step_tokens = getattr(usage, 'total_tokens', 0)
            step_cost = getattr(cost, 'total_cost_usd', 0.0) if cost else 0.0
            
            total_tokens += step_tokens
            total_cost += step_cost
            
            # Determine output type for display
            output_type = "Agent" if hasattr(output, 'state') else "Model"
            
            print(f" {i:02d} | Type: {output_type:5} | Tokens: {step_tokens:6} | Cost: ${step_cost:.6f}")
        else:
            print(f" {i:02d} | ⚠️ No usage data found for this step.")

    print(
        "─" * 55
        + f"\n TOTAL USAGE    | Tokens: {total_tokens:6} | Cost: ${total_cost:.6f}\n"
        + "═" * 55 + "\n"
    )

    return total_tokens

def log_info(message: str, **kwargs) -> None:
    _log('INFO', message, **kwargs)

def log_warning(message: str, **kwargs) -> None:
    _log('WARNING', message, **kwargs)

def log_error(message: str, **kwargs) -> None:
    _log('ERROR', message, **kwargs)
    
def log_debug(message: str, **kwargs) -> None:
    _log('DEBUG', message, **kwargs)

def log_exception(message: str, **kwargs) -> None:
    _log('EXCEPTION', message, exc_info=True, **kwargs)

def _log(level: str, message: str, exc_info: bool = False, **kwargs) -> None:
    """Internal helper to log structured messages to file and console."""
    import sys
    import traceback
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
    }
    if kwargs:
        log_entry["context"] = kwargs
    # Add traceback for ERROR and EXCEPTION
    if level in ("ERROR", "EXCEPTION") or exc_info:
        raw_trace = traceback.format_exc()
        # Escape double quotes to prevent JSON format issues
        safe_trace = raw_trace.replace('"', "'")
        log_entry["traceback"] = safe_trace
    log_line = json.dumps(log_entry, ensure_ascii=False)
    # Log to file
    if level == 'INFO':
        logging.info(log_line)
    elif level == 'WARNING':
        logging.warning(log_line)
    elif level == 'ERROR':
        logging.error(log_line)
    elif level == 'DEBUG':
        logging.debug(log_line)
    elif level == 'EXCEPTION':
        logging.exception(log_line, exc_info=exc_info)
    # Send email for critical errors
    if level in ("ERROR", "EXCEPTION"):
        try:
            import re
            # Sanitize subject and body to avoid header errors
            raw_subject = f"[BeeAI Agent] CRITICAL ERROR: {message[:60]}"
            safe_subject = re.sub(r'[\r\n]+', ' ', str(raw_subject)).replace('"', "'").replace("\"", "'")
            raw_trace = log_entry.get('traceback', '')
            safe_trace = str(raw_trace).replace('"', "'").replace("\"", "'")
            safe_message = str(message).replace('"', "'").replace("\"", "'")
            safe_context = json.dumps(kwargs, ensure_ascii=False).replace('"', "'").replace("\"", "'") if kwargs else ''
            body = (
                f"<b>Timestamp:</b> {log_entry['timestamp']}<br>"
                f"<b>Level:</b> {level}<br>"
                f"<b>Message:</b> {safe_message}<br>"
                f"<b>Traceback:</b><pre>{safe_trace}</pre>"
                f"<b>Context:</b> {safe_context}"
            )
            send_email(
                email="tojimato@gmail.com",
                subject=safe_subject,
                body=body,
                sender_name="BeeAI Agent Logger"
            )
        except Exception as email_exc:
            logging.error(f"Failed to send error email: {email_exc}")
    # Always print to console
    print(f"[{level}] {log_entry['timestamp']} - {message}", file=sys.stderr if level in ('ERROR','EXCEPTION') else sys.stdout)
    if kwargs:
        print(f"  Context: {kwargs}", file=sys.stderr if level in ('ERROR','EXCEPTION') else sys.stdout)
    if level in ("ERROR", "EXCEPTION") or exc_info:
        print(log_entry["traceback"], file=sys.stderr)
