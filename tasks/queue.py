from celery import Celery
from src.config.professions import Profession
from src.config.settings import REDIS_URL

import asyncio
from src.utils.email_service import send_email
from src.pipelines.strategic_pipeline import StrategicPipeline, PipelineOutput
from src.report.report_generator import render_html_from_pipeline_output

app = Celery('beeai', broker=REDIS_URL)

@app.task
def send_daily_report(email: str, profession: Profession, name: str):
    pipeline = StrategicPipeline(profession=profession)
    output: PipelineOutput = asyncio.run(pipeline.execute())
    body = render_html_from_pipeline_output(output, name)
  
    if hasattr(profession, 'value'):
        profession_str = profession.value
    else:
        profession_str = str(profession)
    
    subject = f"Your Daily {profession_str.replace('_', ' ').title()} Report"
    send_email(email, subject, body, sender_name=name)
