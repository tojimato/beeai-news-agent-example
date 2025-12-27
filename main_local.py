"""Strategic Intelligence Agent for autonomous market analysis and reporting.

This module implements a multi-stage LLM pipeline that aggregates market data
from RSS feeds, distills insights, and generates strategic recommendations for
solo developers using the BeeAI framework.

Pipeline stages:
  1. Fetch & Filter: Aggregate relevant news from RSS feeds with keyword scoring
  2. Distill: Extract structured facts and remove noise
  3. Analyze: Build strategic report with market synthesis
  4. Review: Peer-review report for high-conviction opportunities

Environment: Uses .env.local for API keys and model selection via config.py
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Any

import feedparser

import config
from beeai_framework.backend import ChatModel, ChatModelParameters, SystemMessage, UserMessage
from beeai_framework.logger import Logger

from logger_utils import log_token_usage, summarize_total_usage
from report_utils import save_as_html


class StrategicConsultant:
    """Multi-stage LLM pipeline for strategic market intelligence generation.
    
    Attributes:
        MAX_FEED_SEARCH: Maximum RSS entries to scan per source for relevance
        MAX_ENTRIES_PER_SOURCE: Relevant entries to extract per source
        MAX_SUMMARY_WORDS: Word limit for entry summaries (token optimization)
        RSS_SOURCES: Dictionary mapping source names to RSS feed URLs
        VALUABLE_KEYWORDS: Keywords indicating high-quality strategic content
        NOISE_KEYWORDS: Keywords indicating low-quality/irrelevant content
    """

    # --- Configuration Constants ---
    MAX_FEED_SEARCH: int = 15
    MAX_ENTRIES_PER_SOURCE: int = 5
    MAX_SUMMARY_WORDS: int = 100

    # Keywords for content quality filtering
    VALUABLE_KEYWORDS: set[str] = {
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

    NOISE_KEYWORDS: set[str] = {
        'crossword', 'puzzle', 'sudoku', 'quiz', 'recipe', 'lifestyle',
        'daily crossword', 'horoscope', 'contest', 'giveaway'
    }

    RSS_SOURCES: dict[str, str] = {
        # Strategy & Consulting (Corporate Signals)
        "McKinsey_Insights": "https://www.mckinsey.com/insights/rss",
        "Forrester_Strategy": "https://www.forrester.com/blogs/feed/",
        # Tech & Innovation (Future Trends)
        "MIT_Innovation": "https://www.technologyreview.com/feed/",
        "Hacker_News": "https://hnrss.org/frontpage",
        "The_Verge": "https://www.theverge.com/rss/index.xml",
        # Solo-Dev & Startup (Actionable Ideas)
        "Indie_Hackers": "https://ihrss.io/featured",
        # Finance & Crypto (Investment & Risk)
        "CoinTelegraph": "https://cointelegraph.com/rss",
        "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
        "MarketWatch_Macro": "https://www.marketwatch.com/rss/topstories",
    }

    def __init__(self) -> None:
        """Initialize LLM models for the strategic analysis pipeline.
        
        Creates three specialized ChatModel instances:
        - distiller_llm: Fast, lightweight model for data reduction
        - analyzer_llm: Powerful model for strategic synthesis
        - reviewer_llm: Specialized model for critical analysis
        """
        self.distiller_llm: ChatModel = ChatModel.from_name(
            config.GROQ_LLAMA_8B_MODEL,
            ChatModelParameters(temperature=0),
        )
        self.analyzer_llm: ChatModel = ChatModel.from_name(
            config.GROQ_STRATEGY_MODEL,
            ChatModelParameters(temperature=0.2),
        )
        self.reviewer_llm: ChatModel = ChatModel.from_name(
            config.GEMINI_REVIEWER_MODEL,
            ChatModelParameters(temperature=0.1),
        )

    # --- Prompt Management ---

    def _get_strategist_instructions(self) -> str:
        """Generate system prompt for strategic report generation.
        
        Returns:
            String containing detailed instructions for strategic analysis step.
        """
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

    def _get_distiller_instructions(self) -> str:
        """Generate system prompt for data distillation step.
        
        Returns:
            String containing instructions for extracting structured facts.
        """
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

    def _get_reviewer_instructions(self) -> str:
        """Generate system prompt for peer-review step.
        
        Returns:
            String containing instructions for critical analysis of report.
        """
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

    # --- Data Processing ---

    @staticmethod
    def _truncate_by_words(text: str, word_limit: int) -> str:
        """Truncate text to a maximum word count.
        
        Args:
            text: Text to truncate.
            word_limit: Maximum number of words to keep.
        
        Returns:
            Truncated text with ellipsis appended if exceeding limit.
        """
        words: list[str] = text.split()
        if len(words) <= word_limit:
            return text
        return " ".join(words[:word_limit]) + "..."

    @staticmethod
    @staticmethod
    def clean_html(text: str | None) -> str:
        """Remove HTML tags and entities to reduce token usage.
        
        Strips HTML markup, decodes common HTML entities (&nbsp;, &amp;, &quot;),
        and collapses whitespace for token optimization.
        
        Args:
            text: Raw HTML/text string to clean.
        
        Returns:
            Cleaned plain text with normalized whitespace.
        """
        if not text:
            return ""

        # Remove all HTML tags
        html_pattern = re.compile('<.*?>')
        text = re.sub(html_pattern, '', text)

        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')

        # Normalize whitespace (token optimization)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    async def _filter_feed_entries(
        self,
        feed_entries: list[Any],
        max_search: int,
        max_extract: int
    ) -> list[Any]:
        """Filter RSS feed entries by relevance using keyword scoring.
        
        Implements a quality gate: excludes noise keywords, then scores entries
        based on valuable keywords in title and summary. Fallback fills remaining
        slots with non-noise entries if quota not reached.
        
        Args:
            feed_entries: Raw list of RSS feed entry objects.
            max_search: Maximum entries to scan from the feed.
            max_extract: Target number of relevant entries to extract.
        
        Returns:
            List of high-quality relevant entries (max_extract or fewer).
        """
        relevant_entries: list[Any] = []

        for entry in feed_entries[:max_search]:
            if len(relevant_entries) >= max_extract:
                break

            title_lower: str = entry.title.lower()
            summary_raw: str = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            summary_clean: str = self.clean_html(summary_raw).lower()

            # Reject noise entries
            if any(noise in title_lower for noise in self.NOISE_KEYWORDS):
                continue

            # Score by valuable keywords
            score: int = sum(
                1 for word in self.VALUABLE_KEYWORDS
                if word in title_lower or word in summary_clean
            )

            # Selection logic: take scored entries, or fill gaps with non-noise
            is_at_tail_of_search: bool = feed_entries.index(entry) > (max_search * 0.7)
            if score >= 1 or (len(relevant_entries) < max_extract and is_at_tail_of_search):
                relevant_entries.append(entry)

        return relevant_entries

    async def fetch_feeds(self) -> str:
        """Aggregate and filter RSS feeds to extract relevant news content.
        
        For each RSS source:
        1. Parse the feed
        2. Filter entries for relevance using keyword scoring
        3. Clean HTML and truncate summaries
        4. Aggregate into a single formatted string
        
        Returns:
            Formatted string of aggregated relevant news entries, grouped by source.
        """
        aggregated_content: str = ""

        print("\n" + "═" * 60)
        print("📡 SMART DATA ACQUISITION")
        print("═" * 60)

        for source_name, feed_url in self.RSS_SOURCES.items():
            try:
                feed: Any = feedparser.parse(feed_url)
                if not feed.entries:
                    continue

                relevant_entries: list[Any] = await self._filter_feed_entries(
                    feed.entries,
                    self.MAX_FEED_SEARCH,
                    self.MAX_ENTRIES_PER_SOURCE
                )

                print(f"✅ {source_name}: Found {len(relevant_entries)} relevant items")
                aggregated_content += f"\n--- SOURCE: {source_name} ---\n"

                for entry in relevant_entries:
                    summary: str = self._truncate_by_words(
                        self.clean_html(getattr(entry, 'summary', '')),
                        self.MAX_SUMMARY_WORDS
                    )
                    aggregated_content += f"TITLE: {entry.title}\nCONTENT: {summary}\n"

            except Exception as e:
                print(f"⚠️ Error fetching {source_name}: {e}")

        return aggregated_content

    async def run_pipeline(self) -> None:
        """Execute the full strategic intelligence pipeline.
        
        Orchestrates the 4-stage pipeline:
        1. Fetch & filter RSS feeds
        2. Distill raw data into structured facts
        3. Analyze and synthesize strategic report
        4. Peer-review report for high-conviction opportunities
        
        Logs token usage for each stage and saves final report as HTML.
        """
        logger: Logger = Logger("StrategicAgent", level="TRACE")

        # Stage 1: Aggregate and filter raw data
        print("\n📡 STAGE 1: Aggregating market feeds...")
        raw_data: str = await self.fetch_feeds()

        # Stage 2: Distill insights into structured facts
        print("\n🧠 STAGE 2: Distilling insights...")
        distiller_response: Any = await self.distiller_llm.run(
            [
                SystemMessage(self._get_distiller_instructions()),
                UserMessage(f"Distill this raw feed data:\n\n{raw_data}")
            ]
        ).observe(
            lambda emitter: emitter.on(
                "*",
                lambda data, event: logger.info(
                    f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
                )
            )
        )

        distilled_data: str = distiller_response.get_text_content()
        log_token_usage(distiller_response, "Distilling Process")

        print(f"\n--- DEBUG: Distilled Data ---\n{distilled_data}...\n---\n")

        # Stage 3: Build strategic report
        print("📊 STAGE 3: Building strategic report...")
        final_response: Any = await self.analyzer_llm.run(
            [
                SystemMessage(self._get_strategist_instructions()),
                UserMessage(f"Using these distilled facts, build the final report:\n\n{distilled_data}")
            ]
        ).observe(
            lambda emitter: emitter.on(
                "*",
                lambda data, event: logger.info(
                    f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
                )
            )
        )

        report_content: str = final_response.get_text_content()
        log_token_usage(final_response, "Formatting & Translation")

        # Stage 4: Peer-review for high-conviction plays
        print("\n🕵️ STAGE 4: Peer-reviewing strategy...")
        review_response: Any = await self.reviewer_llm.run(
            [
                SystemMessage(self._get_reviewer_instructions()),
                UserMessage(f"Critique and find the highest conviction plays in this report:\n\n{report_content}")
            ]
        ).observe(
            lambda emitter: emitter.on(
                "*",
                lambda data, event: logger.info(
                    f"🔍 EVENT: {event.path} | Target: {type(event.creator).__name__} | Data: {data}"
                )
            )
        )

        review_analysis: str = review_response.get_text_content()
        log_token_usage(review_response, "Peer Review")

        # Aggregate and save final report
        full_report: str = (
            f"{report_content}\n\n---\n## 🕵️ Executive Review & Stress Test\n{review_analysis}"
        )
        timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file: str = save_as_html(full_report, f"Strategy_Report_{timestamp}")

        summarize_total_usage(distiller_response, final_response, review_response)
        print(f"\n📄 Report generated: {os.path.abspath(html_file)}")

# --- Entry Point ---


async def main() -> None:
    """Main entry point for the strategic intelligence agent.
    
    Initializes the StrategicConsultant and runs the full pipeline.
    Suppresses asyncio debug logging to focus on application output.
    """
    # Suppress asyncio debug logs
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)

    agent: StrategicConsultant = StrategicConsultant()
    await agent.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())