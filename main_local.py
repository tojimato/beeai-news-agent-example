import os
import asyncio
import logging
import feedparser
from datetime import datetime
import config

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.backend import ChatModel, ChatModelParameters
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware

from logger_utils import log_token_usage, summarize_total_usage
from report_utils import save_as_html

class StrategicConsultant:
    # --- CONFIGURATION
    MAX_ENTRIES_PER_SOURCE = 3
    MAX_SUMMARY_WORDS = 30  # Kelime bazlı kısıtlama (daha anlamlı kesitler için)
    RSS_SOURCES = {
        "McKinsey_Insights": "https://www.mckinsey.com/insights/rss",
        "Forrester_Strategy": "https://www.forrester.com/blogs/feed/",
        "MIT_Innovation": "https://www.technologyreview.com/feed/",
        "Crypto_News": "https://cointelegraph.com/rss" 
    }
    
    def __init__(self):
        self.llm = ChatModel.from_name(
            config.OPENAI_CHEAPEST_MODEL, 
            ChatModelParameters(temperature=0.2) # Analiz için hafif yaratıcılık
        )
        self.translator_llm = ChatModel.from_name(
            config.OPENAI_CHEAPEST_MODEL, 
            ChatModelParameters(temperature=0) # Çeviri için sıfır sapma
        )

    # --- PROMPT MANAGEMENT ---
    def get_strategic_instructions(self):
        return """You are a Solo-Entrepreneur Business Consultant & Tech Analyst.
        Your goal is to extract high-yield business opportunities for a solo software developer.
        
        FOCUS AREAS:
        1. Micro-SaaS & AI Wrappers: Small, focused tools solving specific problems.
        2. API-First Products: Tools that other developers can integrate.
        3. Low-Overhead Niches: Sectors with high ROI and minimal infrastructure needs.
        4. Macro-Investment Sync: How tech trends align with Gold, Silver, and Crypto.

        OUTPUT: English, raw analytical insights, and specific 'Solo-Dev Opportunities'."""

    def get_analysis_prompt(self, data):
        return f"""Analyze the provided news for Q1 2026. 
        Specifically, identify 3 'Blue Ocean' business opportunities for a solo developer based on these trends.
        
        Data: {data}"""

    def get_translation_instructions(self):
        """
        Bu ajan hem çeviri yapar hem de Markdown yapısını (iskeleti) inşa eder.
        """
        return """You are a professional Financial Editor & Markdown Expert.
        
        TASK:
        1. Translate the provided analysis into Turkish.
        2. Convert the content into a BEAUTIFUL Markdown report.
        
        STRUCTURE REQUIREMENTS:
        - Use # for the main title.
        - Use ## for sections like (Pazar Analizi, Solo Developer Fırsatları, Yatırım Portföyü).
        - Use a Markdown TABLE for the Portfolio: | Varlık | Strateji | Risk Skoru |
        - Use Bullet Points for the 90-day action plan.
        - Highlight key terms with **bold**.
        - Technical terms in (parentheses).

        Output ONLY the final Markdown report in Turkish."""
    
    def _truncate_by_words(self, text, limit):
        """Metni kelime sayısına göre keser."""
        words = text.split()
        if len(words) > limit:
            return " ".join(words[:limit]) + "..."
        return text
    
    # --- DATA & AGENT FLOW ---
    async def fetch_feeds(self):
        """
        Verileri çeker, detaylı loglar ve kaynak bilgisini 
        Agent'ın göreceği şekilde context'e ekler.
        """
        aggregated_content = ""
        # Kaynakları takip etmek için bir liste tutalım
        sourced_meta = [] 

        print("\n" + "═"*60)
        print(f"📡 DATA ACQUISITION - {datetime.now().strftime('%H:%M:%S')}")
        print("═"*60)

        for name, url in self.RSS_SOURCES.items():
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    print(f"❌ {name.ljust(20)} | No data found.")
                    continue

                print(f"✅ {name.ljust(20)} | Processing {len(feed.entries[:self.MAX_ENTRIES_PER_SOURCE])} articles...")
                
                source_section = f"\n[SOURCE: {name} | URL: {url}]\n"
                
                for i, entry in enumerate(feed.entries[:self.MAX_ENTRIES_PER_SOURCE], 1):
                    title = entry.title
                    link = entry.link
                    summary = getattr(entry, 'summary', entry.get('description', ''))
                    clean_summary = self._truncate_by_words(summary, self.MAX_SUMMARY_WORDS)
                    
                    # Terminale detaylı basıyoruz
                    print(f"   └─ {i}. {title[:60]}...")
                    
                    # Agent'a gidecek context bilgisini oluşturuyoruz
                    source_section += (
                        f"ARTICLE {i}:\n"
                        f"- Title: {title}\n"
                        f"- Link: {link}\n"
                        f"- Content: {clean_summary}\n\n"
                    )

                aggregated_content += source_section
                sourced_meta.append(name)

            except Exception as e:
                print(f"⚠️ {name.ljust(20)} | Error: {str(e)[:50]}")

        print("═"*60)
        print(f"📥 Integration complete for: {', '.join(sourced_meta)}")
        print("═"*60 + "\n")
        
        return aggregated_content

    async def run_pipeline(self):
        # 1. Veri Hazırlığı
        raw_data = await self.fetch_feeds()
        
        # 2. ANALİZ ADIMI (Ham Veri İşleme)
        strategy_agent = RequirementAgent(
            llm=self.llm,
            memory=UnconstrainedMemory(),
            instructions=self.get_strategic_instructions()
        )

        print("\n🧠 Analyzing data (Raw Analysis)...")
        strategy_response = await strategy_agent.run(self.get_analysis_prompt(raw_data))
        raw_analysis = strategy_response.last_message.text
        log_token_usage(strategy_response, "Raw Analysis")

        # 3. ÇEVİRİ VE FORMATLAMA ADIMI
        # Burada doğrudan model çağrısı (Direct Call) veya 1 iterasyonluk ajan kullanıyoruz
        translator_agent = RequirementAgent(
            llm=self.translator_llm,
            memory=UnconstrainedMemory(),
            instructions=self.get_translation_instructions()
        )

        print("🔠 Formatting and Translating to Turkish...")
        # Modele ham analizi verip "Bunu güzel bir rapora dönüştür" diyoruz
        translation_query = f"Format and translate this analysis:\n\n{raw_analysis}"
        final_response = await translator_agent.run(translation_query, max_iterations=1)
        
        turkish_report = final_response.last_message.text
        log_token_usage(final_response, "Translation & Formatting")
        
        # 4. KAYIT VE ÇIKTI
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Strategy_Report_TR_{timestamp}"
        html_file = save_as_html(turkish_report, filename)
        
        summarize_total_usage(strategy_response, final_response)
        print(f"\n📄 Rapor Hazır: {os.path.abspath(html_file)}")

# --- ENTRY POINT ---
async def main():
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    app = StrategicConsultant()
    await app.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())