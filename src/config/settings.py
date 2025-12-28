"""Application settings and environment configuration.

This module loads environment variables from .env.local and defines
core application constants for RSS feed aggregation and data processing.
"""

import os
from typing import Final

from dotenv import load_dotenv

# Load environment variables from .env.local file (secrets, API keys)
load_dotenv(".env.local")

# ============================================================================
# RSS Feed Configuration
# ============================================================================

RSS_SOURCES: Final[dict[str, str]] = {
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

# ============================================================================
# Feed Processing Configuration
# ============================================================================

MAX_FEED_SEARCH: Final[int] = 15
"""Maximum RSS entries to scan per source for relevance scoring."""

MAX_ENTRIES_PER_SOURCE: Final[int] = 5
"""Target number of relevant entries to extract per RSS source."""

MAX_SUMMARY_WORDS: Final[int] = 100
"""Word limit for entry summaries to optimize token usage."""

# ============================================================================
# Content Filtering Keywords
# ============================================================================

VALUABLE_KEYWORDS: Final[set[str]] = {
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
"""Keywords indicating high-quality, strategic content."""

NOISE_KEYWORDS: Final[set[str]] = {
    'crossword', 'puzzle', 'sudoku', 'quiz', 'recipe', 'lifestyle',
    'daily crossword', 'horoscope', 'contest', 'giveaway'
}
"""Keywords indicating low-quality or irrelevant content to exclude."""

# ============================================================================
# Output Configuration
# ============================================================================

REPORTS_DIR: Final[str] = "reports"
"""Directory where generated reports are saved."""

LOG_FILE: Final[str] = "agent_usage.log"
"""File path for token usage and cost logging."""
