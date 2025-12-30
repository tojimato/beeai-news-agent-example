import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
import redis

from src.config.professions import Profession
from src.config.settings import REDIS_URL
from src.utils.email_service import send_email
from src.pipelines.strategic_pipeline import StrategicPipeline, PipelineOutput
from src.report.report_generator import render_html_from_pipeline_output

REDIS_RATE_LIMIT_KEY = "last_email_sent_time"
RATE_LIMIT_SECONDS = 120

# Global Redis connection (reuse for all calls)
_redis_instance = redis.Redis.from_url(REDIS_URL)

def wait_for_rate_limit(redis_url: str = REDIS_URL) -> None:
    """Waits if the last email was sent less than RATE_LIMIT_SECONDS ago, with Redis-based distributed lock."""
    lock_key = "last_email_lock"
    lock_ttl = 160  # seconds, lock auto-expires
    r = _redis_instance
    while True:
        # Try to acquire lock atomically
        if r.set(lock_key, "1", nx=True, ex=lock_ttl):
            break
        
        print("Another process holds the lock, waiting...")
        time.sleep(1)
        
    try:
        print(f"Rate limit function called with REDIS_URL: {redis_url}")
        last_sent = r.get(REDIS_RATE_LIMIT_KEY)
        now = int(time.time())
        if last_sent is not None:
            last_sent = int(last_sent)
            elapsed = now - last_sent
            if elapsed < RATE_LIMIT_SECONDS:
                print(f"Rate limit enforced: waiting {RATE_LIMIT_SECONDS - elapsed} seconds before sending email.")
                time.sleep(RATE_LIMIT_SECONDS - elapsed)
        r.set(REDIS_RATE_LIMIT_KEY, int(time.time()))
    finally:
        r.delete(lock_key)

def send_daily_report(email: str, profession, name: str):
    # Convert profession from str to Profession enum if needed
    if isinstance(profession, str):
        try:
            from src.config.professions import Profession as ProfessionEnum
            profession_enum = ProfessionEnum(profession.upper())
        except Exception:
            # Try value-based lookup
            profession_enum = None
            for p in ProfessionEnum:
                if p.value == profession:
                    profession_enum = p
                    break
            if profession_enum is None:
                print(f"Unknown profession: {profession}, using as string.")
                profession_enum = profession
        profession = profession_enum
        
    print(f"Job triggered for {email}, {profession}, {name}")    
    wait_for_rate_limit()
    print(f"Continuing to send report for {email}, {profession}, {name}")    
   
    pipeline = StrategicPipeline(profession=profession)
    output: PipelineOutput = asyncio.run(pipeline.execute())
    body = render_html_from_pipeline_output(output, name)
  
    if hasattr(profession, 'value'):
        profession_str = profession.value
    else:
        profession_str = str(profession)
    
    subject = f"Your Daily {profession_str.replace('_', ' ').title()} Report"
    send_email(email, subject, body, sender_name=name)
