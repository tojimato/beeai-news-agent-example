import json
import logging
import config
from datetime import datetime

# Dosyaya loglama ayarı
logging.basicConfig(
    filename='agent_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def log_token_usage(run_output, task_name="Strategy_Analysis"):
    """
    BeeAI RequirementAgent çıktı şemasına (usage ve cost objelerine) 
    göre optimize edilmiş loglama fonksiyonu.
    """
    
    # 1. Usage bilgilerini al (Objeden doğrudan çekiyoruz)
    usage = getattr(run_output, 'usage', None)
    cost = getattr(run_output, 'cost', None)
    
    # Verileri ayıkla (Çıktına göre eşleşen alanlar)
    prompt_t = usage.prompt_tokens if usage else 0
    completion_t = usage.completion_tokens if usage else 0
    total_t = usage.total_tokens if usage else 0
    cached_t = getattr(usage, 'cached_prompt_tokens', 0)
    
    # Maliyet bilgilerini al
    total_cost = cost.total_cost_usd if cost else 0

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "task": task_name,
        "tokens": {
            "prompt": prompt_t,
            "completion": completion_t,
            "total": total_t,
            "cached": cached_t
        },
        "cost_usd": total_cost,
        "model": config.GROQ_MODEL_NAME
    }
    
    # Konsola profesyonel özet bas
    print(f"\n📊 [TOKEN & COST REPORT - {task_name}]")
    print(f"   Tokens: {total_t} (In: {prompt_t} | Out: {completion_t} | Cached: {cached_t})")
    print(f"   Maliyet: ${total_cost:.6f}")
    print(f"   Durum: {'✅ Başarılı' if total_t > 0 else '⚠️ Bilgi alınamadı'}")
    
    # Dosyaya JSON formatında yaz
    logging.info(json.dumps(log_data))
    
    return log_data