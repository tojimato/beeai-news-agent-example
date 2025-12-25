import json
import logging
from datetime import datetime

# Dosyaya loglama ayarı
logging.basicConfig(
    filename='agent_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def _extract_metrics(output):
    """
    Farklı çıktı tiplerinden (RequirementAgentOutput veya ChatModelOutput)
    usage ve cost bilgilerini ayıklayan yardımcı iç fonksiyon.
    """
    # 1. RequirementAgentOutput yapısı (state objesi içerir)
    if hasattr(output, 'state'):
        usage = getattr(output.state, 'usage', None)
        cost = getattr(output.state, 'cost', None)
    # 2. ChatModelOutput yapısı (doğrudan kullanım)
    else:
        usage = getattr(output, 'usage', None)
        cost = getattr(output, 'cost', None)
    
    return usage, cost

def log_token_usage(run_output, task_name="Task_Execution"):
    """
    Hem Ajan hem de ChatModel çıktılarını destekleyen polimorfik loglama fonksiyonu.
    """
    usage, cost = _extract_metrics(run_output)
    
    # Verileri güvenli şekilde ayıkla
    prompt_t = getattr(usage, 'prompt_tokens', 0) if usage else 0
    completion_t = getattr(usage, 'completion_tokens', 0) if usage else 0
    total_t = getattr(usage, 'total_tokens', 0) if usage else 0
    cached_t = getattr(usage, 'cached_prompt_tokens', 0) if usage else 0
    
    # Maliyet bilgilerini al
    total_cost = getattr(cost, 'total_cost_usd', 0.0) if cost else 0.0

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
    Karma (Ajan ve Model) çıktı listesini toplar ve özet rapor sunar.
    """
    total_tokens = 0
    total_cost = 0.0
    
    print("\n" + "═"*55)
    print(f"📈 AGGREGATED USAGE SUMMARY | {datetime.now().strftime('%H:%M:%S')}")
    print("─"*55)

    for i, output in enumerate(run_outputs, 1):
        usage, cost = _extract_metrics(output)

        if usage:
            t_tokens = getattr(usage, 'total_tokens', 0)
            t_cost = getattr(cost, 'total_cost_usd', 0.0) if cost else 0.0
            
            total_tokens += t_tokens
            total_cost += t_cost
            
            # Çıktı tipini belirle (Debug görseli için)
            output_type = "Agent" if hasattr(output, 'state') else "Model"
            
            print(f" {i:02d} | Type: {output_type:5} | Tokens: {t_tokens:6} | Cost: ${t_cost:.6f}")
        else:
            print(f" {i:02d} | ⚠️ No usage data found for this step.")

    print("─"*55)
    print(f" TOTAL USAGE    | Tokens: {total_tokens:6} | Cost: ${total_cost:.6f}")
    print("═"*55 + "\n")

    return total_tokens