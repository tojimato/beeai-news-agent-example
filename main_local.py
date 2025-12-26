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
        # STRATEGY & CONSULTING (Kurumsal Sinyaller)
        "McKinsey_Insights": "https://www.mckinsey.com/insights/rss", # Aktif
        "Forrester_Strategy": "https://www.forrester.com/blogs/feed/", # Aktif
        
        # TECH & INNOVATION (Gelecek Trendleri)
        "MIT_Innovation": "https://www.technologyreview.com/feed/", # Aktif
        "Hacker_News": "https://hnrss.org/frontpage", # (hnrss.org en stabil HN servisidir)
        "The_Verge": "https://www.theverge.com/rss/index.xml", # Aktif
        
        # SOLO-DEV & STARTUP (Uygulanabilir Fikirler)
        "Indie_Hackers": "https://ihrss.io/featured", # (ihrss.io, resmi olmayan ama en stabil IH feed'idir)
        
        # FINANCE & CRYPTO (Yatırım ve Risk)
        "CoinTelegraph": "https://cointelegraph.com/rss", # Aktif
        "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex", # Reuters yerine en iyi alternatif
        "MarketWatch_Macro": "https://www.marketwatch.com/rss/topstories", # Ekonomik makro görünüm için
    }
    
    def __init__(self):
        
        self.distiller_llm = ChatModel.from_name(
            config.GROQ_LLAMA_8B_MODEL, 
            ChatModelParameters(temperature=0),
        )
        
        self.analyzer_llm = ChatModel.from_name(
            config.GROQ_STRATEGY_MODEL, 
            ChatModelParameters(temperature=0.2),
        )
        
        self.reviewer_llm = ChatModel.from_name(
            config.GEMINI_REVIEWER_MODEL, 
            ChatModelParameters(temperature=0.1),
        )

    # --- PROMPT MANAGEMENT (STRUCTURED OUTPUT) ---
    def get_strategist_instructions(self):
        """Adım 2: Stratejik Mimar - Rafine veriden zenginleştirilmiş yol haritası inşa eder."""
        return """You are a Senior Strategic Analyst and Report Architect. 
        Your goal: Synthesize distilled facts into a high-density roadmap for a Solo Developer. 
        Fill data gaps using your internal knowledge of global market cycles, institutional trends (McKinsey/Goldman style), and technical evolution.

        STRICT REPORT TEMPLATE:
        # 🚀 STRATEGIC INTELLIGENCE REPORT
        *Generated on: {Date}*

        ## 🌍 Market Pulse & Sentiment Analysis
        > {Deep 4-5 sentence synthesis. Analyze the 'Collision' between macro trends and technical shifts. Explain not just what is happening, but why it matters for small-scale capital.}

        ---
        ## 🛠️ Build Opportunities (Solo-Dev Focus)
        {Identify 5-6 actionable project ideas. Use this format:}
        ### 💡 [Project Name]
        * **Strategic Logic:** {Deep explanation. Why is there a vacuum in the market for this right now?}
        * **Tech Stack:** `{Specific frameworks, specialized APIs, or infrastructure}`
        * **Execution Complexity:** {1-10}/10 | **Est. Time to MVP:** {e.g., 3 weeks}

        ---
        ## 📈 Detailed Financial Strategy & Asset Allocation
        {Expand the table. Analyze the underlying macro drivers for each asset.}
        | Asset | Macro Catalyst & Outlook | Strategic Positioning | Risk Level |
        | :--- | :--- | :--- | :--- |
        | **Gold** | {Inflation/Geopolitical context} | {Physical vs. Digital hedge} | 🟢 Low |
        | **Silver** | {Industrial/Solar/EV demand} | {Speculative/Long-term holding} | 🟡 Med |
        | **Bitcoin** | {Liquidity/Halving/Institutional flow} | {Exit/Entry triggers} | 🔴 High |
        | **Tech Stocks** | {AI/Semiconductor cycle} | {Overweight/Underweight sectors} | 🟡 Med |
        | **Commodities** | {Energy/Oil/Supply chain risk} | {Trading vs. Investing approach} | 🔴 High |

        ---
        ## 💡 Advanced Strategic Recommendations
        {Provide 5 comprehensive strategic moves. Focus on moat-building and scalability.}
        1. **High-Priority Pivot:** {Most urgent adjustment to current operations}
        2. **Technical Hedge:** {Which emerging stack or skill ensures future-proofing?}
        3. **Monetization Strategy:** {Specific pricing model for the build opportunities above}
        4. **Distribution Hack:** {A low-cost way to find the first 100 users in this climate}
        5. **Long-term Moat:** {How to protect a solo-dev project from being cloned by AI}

        ---
        *Disclaimer: Strategic insights for educational purposes only. Predictive logic used to enrich sparse data.*
        """

    def get_analysis_prompt(self, data):
        return f"Extract structured insights from this data:\n\n{data}"

    def get_distiller_instructions(self):
        return """You are a Data Distiller. 
        Your goal is to strip away the fluff from news entries and extract only technical facts and financial data points.

        TASKS:
        1. Group related news.
        2. Extract specific numbers, tech stacks, and regulatory mentions.
        3. Output in a condensed bullet-point format.

        OUTPUT FORMAT:
        - CATEGORY: <Name>
        - FACTS: <Technical/Financial fact 1>, <Fact 2>
        - KEY_TECHS: <Tools/APIs mentioned>
        """
    def get_reviewer_instructions(self):
        return """You are a Senior Venture Capitalist and Risk Manager. 
        Your task is to critically analyze the provided Strategic Intelligence Report. 
        Don't just repeat the report; evaluate its viability and find the hidden gems.

        CRITICAL ANALYSIS STRUCTURE:
        
        ### 🎯 The "Golden Thread"
        - What is the single most important meta-trend connecting all these points?
        
        ### ⚖️ Risk & Reality Check
        - Which project idea is actually the hardest to pull off for a solo dev? (The "Ugly Truth")
        - Are the financial allocations too aggressive or too passive for the current climate?
        
        ### 💎 High-Conviction Bet
        - If you had $10,000 and 1 month, which ONE project/asset move from this report would you pick? Why?
        
        ### 🛡️ Missing Links
        - What did the strategist overlook? (e.g., a specific regulation, a competitor move, or a hidden cost)
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

        print("\n🧠 STEP 1: Distilling Insights ...")
        
        distiller_response = await self.distiller_llm.run(
            [
                SystemMessage(self.get_distiller_instructions()),
                UserMessage(f"Distill this raw feed data:\n\n{raw_data}")
            ]
        ).observe(lambda emitter: emitter.on(
            "*", lambda data, event: logger.info(
                f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
            )
        ))
             
        distilled_data = distiller_response.get_text_content()
        log_token_usage(distiller_response, "Distilling Process")
        
        # Debug için ara çıktıyı görelim (İsterseniz yorum satırı yapabilirsiniz)
        print(f"\n--- DEBUG: Distilled Data ---\n{distilled_data}...\n---------------------------\n")

        # 3. FORMATLAMA ADIMI (Strategist)
        print("🔠 STEP 2: Building Final Strategic Report ...")
        
        final_response = await self.analyzer_llm.run(
            [
                SystemMessage(self.get_strategist_instructions()),
                UserMessage(f"Using these distilled facts, build the final report:\n\n{distilled_data}")
            ]).observe(lambda emitter: emitter.on(
            "*", lambda data, event: logger.info(
                f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
            )
        ))
             
        report_content = final_response.get_text_content()
        log_token_usage(final_response, "Formatting & Translation")
        
        # 4. ADIM: STRATEJİK YORUMLAMA (Reviewer)
        print("🕵️ STEP 3: Peer-Reviewing the Strategy...")
        review_response = await self.reviewer_llm.run([
            SystemMessage(self.get_reviewer_instructions()),
            UserMessage(f"Critique and find the highest conviction plays in this report:\n\n{report_content}")
        ]).observe(lambda emitter: emitter.on(
            "*", lambda data, event: logger.info(
                f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
            )
        ))
        
        review_analysis = review_response.get_text_content()
        log_token_usage(review_response, "Peer Review")
        
        # 5. KAYIT
        full_report = f"{report_content}\n\n---\n## 🕵️ Executive Review & Stress Test\n{review_analysis}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = save_as_html(full_report, f"Strategy_Report_{timestamp}")
        
        summarize_total_usage(distiller_response, final_response, review_response)
        print(f"\n📄 Rapor ve Kritik Hazır: {os.path.abspath(html_file)}")

# --- ENTRY POINT ---
async def main():
    # Asyncio loglarını sustur, kendi loglarımıza odaklan
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    app = StrategicConsultant()
    await app.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())