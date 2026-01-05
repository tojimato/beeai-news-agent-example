"""Application settings and environment configuration.

This module loads environment variables from .env.local and defines
core application constants for RSS feed aggregation and data processing.
"""

import os
from typing import Final
from enum import Enum

from dotenv import load_dotenv

# Load environment variables from .env.local file (secrets, API keys)
load_dotenv(".env.local")

# ============================================================================
# Redis/Celery Queue Configuration
# ============================================================================

REDIS_URL: Final[str] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# ============================================================================
# RSS Feed Configuration
# ============================================================================

RSS_SOURCES: Final[dict[str, dict[str, str]]] = {
    # Default sources for all professions
    "default": {
        "McKinsey_Insights": "https://www.mckinsey.com/insights/rss",
        "Forrester_Strategy": "https://www.forrester.com/blogs/feed/",
        "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
        "Economist_Business": "https://www.economist.com/business/rss.xml"
    },
    # Example: profession-specific overrides (add as needed)
    "interior_designer": {
        "Dezeen": "https://www.dezeen.com/feed/",
        "ArchDaily": "https://www.archdaily.com/rss",
        "InteriorDesign": "https://www.interiordesign.net/rss/",
        "DesignBoom": "https://www.designboom.com/feed/",
        "DesignMilk": "https://design-milk.com/category/interior-design/feed/",
        "Apartment_Therapy": "https://www.apartmenttherapy.com/feed",
        "Dwell": "https://www.dwell.com/feed/rss",
        "Houzz": "https://www.houzz.com/magazine/feed",
        "Architectural_Digest": "https://www.architecturaldigest.com/feed",
        "Contemporist": "https://www.contemporist.com/feed/",
        "Freshome": "https://www.freshome.com/feed/",
        "Yanko_Design": "https://www.yankodesign.com/feed/",
        "Design_Sponge": "https://www.designsponge.com/feed",
        "Yellowtrace": "https://www.yellowtrace.com.au/feed/",
        "Home_Design_Lover": "https://www.homedesignlover.com/feed/"
    },
    "solo_developer": {
        "InfoQ": "https://feed.infoq.com/",
        "Hacker_News": "https://hnrss.org/frontpage",
        "The_Verge": "https://www.theverge.com/rss/index.xml",
        "MIT_Innovation": "https://www.technologyreview.com/feed/",
        "OpenAI_Blog": "https://openai.com/news/rss.xml",
        "Towards_AI": "https://towardsai.net/feed",
        "IndieHackers": "https://www.indiehackers.com/feed",
        "ProductHunt": "https://www.producthunt.com/feed",
        "Hacker_News": "https://hnrss.org/frontpage"
    }
    # Add more professions as needed
}

def get_rss_sources_for_profession(profession: str) -> dict[str, str]:
    """
    Returns the RSS sources for a given profession. If no specific sources are defined,
    returns the default set.
    Args:
        profession: The profession key (e.g., 'interior_designer') or Profession enum.
    Returns:
        Dictionary of RSS source names to URLs.
    """
    if hasattr(profession, 'value'):
        key = profession.value
    else:
        key = str(profession)
        
    sources = dict(RSS_SOURCES.get("default", {}))
    
    prof_sources = RSS_SOURCES.get(key, {})
    
    sources.update(prof_sources)
    
    return sources

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
    'strategy', 'market', 'innovation', 'growth', 'competitive',
    'analysis', 'trend', 'insight', 'forecast', 'opportunity',
    'business', 'economy', 'technology', 'leadership', 'management',
    'customer', 'productivity', 'efficiency', 'transformation',
    'disruption', 'sustainability', 'digital', 'data', 'ai', 'automation'
}
"""Keywords indicating high-quality, strategic content."""

# Optional profession-specific keyword overrides. Keys match profession keys
# used by `get_rss_sources_for_profession` (string or Enum.value).
VALUABLE_KEYWORDS_BY_PROFESSION: Final[dict[str, set[str]]] = {
    "interior_designer": {
        'interior', 'design', 'architecture', 'lighting', 'material',
        'aesthetic', 'sustainability', 'furniture', 'renovation', 'design', 'interior', 'architecture', 'trend', 'aesthetic', 'concept',
        'space', 'layout', 'material', 'color', 'lighting', 'furniture',
        'decor', 'renovation', 'sustainability', 'functionality', 'innovation',
        'style', 'ambiance', 'visual', 'environment', 'modern', 'classic'
    },
    "solo_developer": {
        'ai', 'saas', 'automation', 'indie', 'solodev', 'startup',
        'llm', 'dev', 'productivity', 'api', 'integration', 'no-code',
        'low-code', 'scalability', 'cloud', 'microservices', 'devops',
        'automation', 'efficiency', 'innovation', 'growth', 'market',
    }
}
"""Optional profession-specific valuable keyword overrides."""


def get_valuable_keywords_for_profession(profession: str | Enum) -> set[str]:
    """
    Return the merged set of valuable keywords for a profession.

    If a profession has no overrides defined, this returns a shallow copy of
    the default `VALUABLE_KEYWORDS` set to preserve backward compatibility.

    Args:
        profession: The profession key (e.g., 'interior_designer') or an
            Enum with a `value` attribute.

    Returns:
        A set of keywords to use for feed relevance scoring.
    """
    if hasattr(profession, 'value'):
        key = profession.value
    else:
        key = str(profession)

    keywords = set(VALUABLE_KEYWORDS)
    prof_keywords = VALUABLE_KEYWORDS_BY_PROFESSION.get(key, set())
    keywords.update(prof_keywords)
    return keywords

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

# ============================================================================
# Email Service Configuration
# ============================================================================

EMAIL_PROVIDER: Final[str] = os.environ.get("EMAIL_PROVIDER", "smtp")
"""Email provider: 'smtp' or 'resend'."""

RESEND_API_KEY: Final[str] = os.environ.get("RESEND_API_KEY", "")
"""API key for Resend email service."""

RESEND_FROM_EMAIL: Final[str] = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
"""From email address for Resend (must be verified domain)."""

SMTP_HOST: Final[str] = os.environ.get("SMTP_HOST", "smtp.gmail.com")
"""SMTP server hostname."""

SMTP_PORT: Final[int] = int(os.environ.get("SMTP_PORT", 465))
"""SMTP server port."""

SMTP_USER: Final[str] = os.environ.get("SMTP_USER", "your@email.com")
"""SMTP authentication username."""

SMTP_PASS: Final[str] = os.environ.get("SMTP_PASS", "yourpassword")
"""SMTP authentication password."""

ALERT_EMAIL: Final[str] = os.environ.get("ALERT_EMAIL", "")
"""Email address for error alerts."""

# ============================================================================
# Language Configuration
# ============================================================================

class Language(Enum):
    TURKISH = "tr"
    ENGLISH = "en"