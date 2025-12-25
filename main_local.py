import os
import asyncio
import logging
import feedparser
import re
from datetime import datetime
import config

# Framework Imports
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.backend import ChatModel, ChatModelParameters, UserMessage, SystemMessage
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.logger import Logger

# Custom Utils
from logger_utils import log_token_usage, summarize_total_usage
from report_utils import save_as_html

class StrategicConsultant:
    # --- CONFIGURATION
    MAX_FEED_SEARCH = 15
    MAX_ENTRIES_PER_SOURCE = 5
    MAX_SUMMARY_WORDS = 100
    RSS_SOURCES = {
        "McKinsey_Insights": "https://www.mckinsey.com/insights/rss",
        "MIT_Innovation": "https://www.technologyreview.com/feed/",
        "Crypto_News": "https://cointelegraph.com/rss",
        "Forrester_Strategy": "https://www.forrester.com/blogs/feed/",
    }
    
    def __init__(self):
        # Analiz için biraz daha esnek parametreler
        self.llm = ChatModel.from_name(
            config.OPENAI_CHEAPEST_MODEL, 
            ChatModelParameters(temperature=0.2),
        )
        # Çeviri ve Formatlama için sıfır hata toleransı
        self.translator_llm = ChatModel.from_name(
            config.OPENAI_CHEAPEST_MODEL, 
            ChatModelParameters(temperature=0),
        )

    # --- PROMPT MANAGEMENT (STRUCTURED OUTPUT) ---
    def get_strategic_instructions(self):
        return """You are a Senior Strategic Analyst specializing in Lean Startups and FinTech.
        Your task: Distill raw news into high-signal strategic intelligence.

        OUTPUT STRUCTURE (STRICT):
        
        [MARKET_SENTIMENT]
        A concise 2-sentence macro view of current trends based on provided data.

        [DEVELOPER_EDGE]
        Identify 3 actionable project ideas. Use format:
        - ID: <Short Name> | Logic: <The 'Why' for a solo dev> | Stack: <Specific Tech/APIs> | Difficulty: <1-10>

        [PORTFOLIO_GUIDE]
        Contextualize financial data for a tech-focused investor.
        Format: Asset | Logic: <Actionable advice> | Risk: <Low/Med/High>
        (Assets: Gold, Silver, BTC, Tech Stocks)

        [IMMEDIATE_ACTIONS]
        - <Actionable item 1>
        - <Actionable item 2>
        - <Actionable item 3>

        GUIDELINE: Be technical, blunt, and avoid fluff. If data is sparse, use your internal knowledge to fill gaps logically.
        """

    def get_analysis_prompt(self, data):
        return f"Extract structured insights from this data:\n\n{data}"

    def get_translation_instructions(self):
        return """You are a Report Architect. 
        Convert the RAW ANALYTIC TEXT into a premium-tier Strategy Report.

        REPORT DESIGN RULES:
        1.  **Title**: Use a bold, unique title based on the date.
        2.  **Executive Summary**: Use a blockquote for the Pulse.
        3.  **Visual Structure**: Use '---' to separate sections.
        4.  **Formatting**: Ensure all Tech names are in `code blocks`.

        MARKET REPORT TEMPLATE:

        # 🚀 STRATEGIC INTELLIGENCE REPORT
        *Generated on: {Date}*

        ## 🌍 Market Pulse
        > {Content from [MARKET_SENTIMENT]}

        ---

        ## 🛠️ Build Opportunities (Solo-Dev Focus)
        {Convert [DEVELOPER_EDGE] into this format:}
        ### 💡 [Project Name]
        * **Strategic Logic:** [Logic]
        * **Tech Stack:** `[Stack]`
        * **Execution Complexity:** [Difficulty]/10

        ---

        ## 📈 Financial Strategy & Risk
        | Asset | Strategic Outlook | Risk Level |
        | :--- | :--- | :--- |
        {Convert [PORTFOLIO_GUIDE] into table rows. Ensure Risk Level uses emojis: 🟢 Low, 🟡 Med, 🔴 High}

        ---

        ## ⚡ Next 7-Day Action Plan
        {Convert [IMMEDIATE_ACTIONS] into a clean checklist}
        - [ ] **Priority 1:** [Action 1]
        - [ ] **Priority 2:** [Action 2]
        - [ ] **Priority 3:** [Action 3]

        ---
        *Disclaimer: Strategic insights for educational purposes only.*
        """

    # --- DATA UTILS ---
    def _truncate_by_words(self, text, limit):
        words = text.split()
        return " ".join(words[:limit]) + "..." if len(words) > limit else text
    
    def clean_html(self, text):
        """
        HTML etiketlerini temizler, &nbsp; gibi karakterleri düzeltir
        ve fazla boşlukları temizleyerek token tasarrufu sağlar.
        """
        if not text:
            return ""
        
        # 1. Tüm HTML etiketlerini kaldır (<img>, <p>, <a> vb.)
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        
        # 2. Yaygın HTML entity'lerini temizle
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
        
        # 3. Birden fazla boşluğu ve satır başlarını tekilleştir (Token tasarrufu)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def fetch_feeds(self):
        aggregated_content = ""
        
        VALUABLE_KEYWORDS = {
            # Software & Entrepreneurship
            'ai', 'saas', 'automation', 'microsaas', 'indie', 'solodev', 'trend', 
            'market', 'opportunity', 'revenue', 'growth', 'future', 'technology', 
            'software', 'dev', 'tool', 'platform', 'startup', 'innovation', 'aeo',
            'scaling', 'efficiency', 'monetization', 'business', 'strategy',
            'no-code', 'low-code', 'api', 'deployment', 'cloud', 'mvp', 'b2b',
            'agentic', 'llm', 'framework', 'productivity', 'workflow',
            
            # Finance & Investment
            'stock', 'equity', 'nasdaq', 'sp500', 'fed', 'inflation', 'interest rate', 
            'dividend', 'portfolio', 'commodity', 'gold', 'silver', 'oil', 'energy',
            'recession', 'economy', 'bull market', 'bear market', 'treasury', 'yield',
            
            # Crypto & Web3
            'crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'blockchain', 'defi', 
            'layer2', 'scaling', 'zk-proof', 'wallet', 'node', 'mining', 'halving', 
            'stablecoin', 'solana', 'altcoin', 'etf', 'liquidity', 'staking'
        }

        # Elenmesi gereken düşük kaliteli veya alakasız içerik tipleri
        NOISE_KEYWORDS = {
            'crossword', 'puzzle', 'sudoku', 'quiz', 'recipe', 'lifestyle', 
            'daily crossword', 'horoscope', 'contest', 'giveaway'
        }

        print("\n" + "═"*60)
        print(f"📡 SMART DATA ACQUISITION")
        print("═"*60)

        for name, url in self.RSS_SOURCES.items():
            try:
                feed = feedparser.parse(url)
                if not feed.entries: continue

                relevant_entries = []
                
                # Kaliteli içerik bulmak için belirlenen limit kadar tara
                for entry in feed.entries[:self.MAX_FEED_SEARCH]: 
                    if len(relevant_entries) >= self.MAX_ENTRIES_PER_SOURCE:
                        break

                    title_lower = entry.title.lower()
                    summary_raw = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    summary_clean = self.clean_html(summary_raw).lower()
                    
                    # 1. Gürültü Kontrolü: Eğer gürültü kelimesi varsa bu haberi tamamen atla
                    if any(noise in title_lower for noise in NOISE_KEYWORDS):
                        continue

                    # 2. Skor Hesaplama
                    score = sum(1 for word in VALUABLE_KEYWORDS if word in title_lower or word in summary_clean)

                    # 3. Seçim Mantığı
                    # Puanı olanları hemen ekle
                    if score >= 1:
                        relevant_entries.append(entry)
                    # Puanı olmasa bile, liste çok boş kaldıysa ve taramanın sonuna geliyorsak doldur (Gürültü olmayanlardan)
                    elif len(relevant_entries) < self.MAX_ENTRIES_PER_SOURCE and feed.entries.index(entry) > (self.MAX_FEED_SEARCH * 0.7):
                        relevant_entries.append(entry)

                print(f"✅ {name}: Found {len(relevant_entries)} relevant items")
                aggregated_content += f"\n--- SOURCE: {name} ---\n"
                
                for entry in relevant_entries:
                    summary = self._truncate_by_words(self.clean_html(getattr(entry, 'summary', '')), self.MAX_SUMMARY_WORDS)
                    aggregated_content += f"TITLE: {entry.title}\nCONTENT: {summary}\n"
                    
            except Exception as e:
                print(f"⚠️ Error {name}: {e}")

        return aggregated_content

    # --- PIPELINE ---
    async def run_pipeline(self):
        # 1. DEBUG LOGGING BAŞLAT
        # TRACE seviyesi ajanın düşüncelerini gösterir
        logger = Logger("StrategicAgent", level="TRACE")
        
        raw_data = await self.fetch_feeds()

        print("\n🧠 STEP 1: Extracting Structured Insights ...")
        
        strategy_response = await self.llm.run(
            [
                SystemMessage(self.get_strategic_instructions()),
                UserMessage(self.get_analysis_prompt(raw_data))
            ]
        ).observe(lambda emitter: emitter.on(
            "*", lambda data, event: logger.info(
                f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
            )
        ))
             
        raw_insights = strategy_response.get_text_content()
        log_token_usage(strategy_response, "Structured Extraction")
        
        # Debug için ara çıktıyı görelim (İsterseniz yorum satırı yapabilirsiniz)
        print(f"\n--- DEBUG: RAW INSIGHTS ---\n{raw_insights}...\n---------------------------\n")

        # 3. FORMATLAMA ADIMI (Direct Call + Markdown Builder)
        print("🔠 STEP 2: Building Markdown Report ...")
        
        final_response = await self.translator_llm.run(
            [
                SystemMessage(self.get_translation_instructions()),
                UserMessage(f"Build the report from this data:\n\n{raw_insights}")
            ])
             
        report_content = final_response.get_text_content()
        log_token_usage(final_response, "Formatting & Translation")
        
        # 4. KAYIT
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = save_as_html(report_content, f"Strategy_Report_{timestamp}")
        
        summarize_total_usage(strategy_response, final_response)
        print(f"\n📄 Rapor Hazır: {os.path.abspath(html_file)}")

# --- ENTRY POINT ---
async def main():
    # Asyncio loglarını sustur, kendi loglarımıza odaklan
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    app = StrategicConsultant()
    await app.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())