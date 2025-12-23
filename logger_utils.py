import json
import logging
from datetime import datetime

# Dosyaya loglama ayarı
logging.basicConfig(
    filename='agent_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def log_token_usage(run_output, task_name="General Task"):
    usage = run_output.usage
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "task": task_name,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "duration_sec": getattr(run_output, 'duration', 0)
    }
    
    # Konsola renkli bas (Geliştirici dostu)
    print(f"\n📊 [TOKEN RAPORU - {task_name}]")
    print(f"   Giriş: {usage.prompt_tokens} | Çıkış: {usage.completion_tokens}")
    print(f"   Toplam: {usage.total_tokens} | Süre: {log_data['duration_sec']:.2f}s")
    
    # Dosyaya yaz (Kalıcı takip)
    logging.info(json.dumps(log_data))
    return log_data