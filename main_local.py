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
            config.OPENAI_TRANSLATOR_MODEL, 
            ChatModelParameters(temperature=0) # Çeviri için sıfır sapma
        )

    # --- PROMPT MANAGEMENT ---
    def get_strategic_instructions(self):
        """Token-optimized Strategic Instructions"""
        return """You are a lean Strategic Advisor for a solo dev. 
        Analyze tech trends and macro-investments (Gold, Silver, Crypto, Tech Stocks).
        Methodology: Data-driven, cynical, focus on high-yield/low-overhead.
        Output: Professional, condensed, and actionable. No fluff."""

    def get_analysis_prompt(self, data):
        """Token-optimized Analysis Prompt"""
        return f"""
        Q1 2026 Strategic Briefing.
        Input Data: {data}

        Requirements:
        1. MARKET SUMMARY: 2-3 sentences max on current sentiment.
        2. PILLARS: 3 tech niches for solo-devs. Format: 'Niche | Why | Action'.
        3. PORTFOLIO: A Markdown Table for Gold, Silver, BTC, and Tech Stocks with 'Asset | Strategy | Risk'.
        4. 90-DAY ROADMAP: 5 bullet points for immediate execution.
        5. SOURCES: List URLs only.

        Constraint: Be concise. Avoid introductory phrases. Use Markdown tables/bullets.
        Language: Professional English.
        """

    def get_translation_instructions(self):
        """Markdown skeleton preserving instructions"""
        return """You are a technical translator. Your ONLY task is to translate English text to Turkish while strictly preserving Markdown syntax.
        
        RULES:
        1. DO NOT modify Markdown structures: keep tables (|---|), headers (#, ##), and bolding (**) exactly as they are.
        2. DO NOT add extra spaces inside table cells that could break the alignment.
        3. Translate the content inside the table cells, but keep the pipes (|) intact.
        4. Keep technical financial terms in parentheses: e.g., 'Liquidity (Likidite)'.
        5. Output ONLY the translated Markdown. No conversational filler."""
    
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
        
        # 2. STRATEJİ AJANI (English Only)
        strategy_agent = RequirementAgent(
            llm=self.llm,
            tools=[ThinkTool()],
            memory=UnconstrainedMemory(),
            instructions=self.get_strategic_instructions(),
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
            requirements=[
                ConditionalRequirement(ThinkTool, min_invocations=1,  max_invocations=2) 
            ]
        )

        print("\n🧠 Strategy Agent is analyzing (English)...")
        strategy_response = await strategy_agent.run(self.get_analysis_prompt(raw_data))
        english_report = strategy_response.last_message.text
        log_token_usage(strategy_response, "Strategy Analysis")
        
        # 3. ÇEVİRİ AJANI (Translator Agent)
        translator_agent = RequirementAgent(
            llm=self.translator_llm,
            memory=UnconstrainedMemory(),
            instructions=self.get_translation_instructions()
        )

        print("🔠 Translator Agent is converting report to Turkish...")
        translation_query = f"Please translate this report: \n\n{english_report}"
        final_response = await translator_agent.run(translation_query, max_iterations = 1)
        turkish_report = final_response.last_message.text
        log_token_usage(final_response, "Translator Agent")
        
        # 4. KAYIT VE ÇIKTI
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]
        filename = f"Strategy_Report_TR_{timestamp}"
        html_file = save_as_html(turkish_report, filename)
        
        # 5. SUMMARIZE USAGE
        summarize_total_usage(strategy_response, final_response)

        print("\n" + "═"*60)
        print(f"📄 Rapor Hazır: {os.path.abspath(html_file)}")
        print("═"*60)

# --- ENTRY POINT ---
async def main():
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    app = StrategicConsultant()
    await app.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())