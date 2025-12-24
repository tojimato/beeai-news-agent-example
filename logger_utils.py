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
    usage = getattr(run_output.state, 'usage', None)
    cost = getattr(run_output.state, 'cost', None)
    
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
        "cost_usd": total_cost
    }
    
    # Konsola profesyonel özet bas
    print(f"\n📊 [TOKEN & COST REPORT - {task_name}]")
    print(f"   Tokens: {total_t} (In: {prompt_t} | Out: {completion_t} | Cached: {cached_t})")
    print(f"   Maliyet: ${total_cost:.6f}")
    print(f"   Durum: {'✅ Başarılı' if total_t > 0 else '⚠️ Bilgi alınamadı'}")
    
    # Dosyaya JSON formatında yaz
    logging.info(json.dumps(log_data))
    
    return log_data

def summarize_total_usage(*run_outputs):
    """
    Birden fazla ajandan gelen çıktıları toplar, ekrana formatlı basar 
    ve toplam token sayısını döndürür.
    """
    total_tokens = 0
    total_cost = 0.0
    
    print("\n" + "═"*45)
    print("📈 AGGREGATED USAGE SUMMARY")
    print("─"*45)

    for i, output in enumerate(run_outputs, 1):
        # log_token_usage içinde kullandığın erişim mantığının aynısı
        usage = getattr(output.state, 'usage', None)
        cost = getattr(output.state, 'cost', None)

        if usage:
            t_tokens = usage.total_tokens
            t_cost = cost.total_cost_usd if cost else 0.0
            
            total_tokens += t_tokens
            total_cost += t_cost
            
            print(f" Agent {i:02d} | Tokens: {t_tokens:6} | Cost: ${t_cost:.6f}")
        else:
            print(f" Agent {i:02d} | ⚠️ No usage data found.")

    print("─"*45)
    print(f" TOTAL    | Tokens: {total_tokens:6} | Cost: ${total_cost:.6f}")
    print("═"*45 + "\n")

    return total_tokens