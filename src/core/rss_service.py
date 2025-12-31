"""RSS feed aggregation and filtering service.

This module implements a single-responsibility service for fetching, parsing,
and filtering RSS feeds based on content relevance scoring.
"""

from typing import Any, Final

import feedparser

from src.config.professions import Profession
from src.config.settings import (
    VALUABLE_KEYWORDS,
    NOISE_KEYWORDS,
    MAX_FEED_SEARCH,
    MAX_ENTRIES_PER_SOURCE,
    MAX_SUMMARY_WORDS,
    get_rss_sources_for_profession,
)
from src.utils.text_processing import clean_html, truncate_text


class RSSService:
    """Service for aggregating and filtering RSS feed content.
    
    Responsibility:
    - Fetch RSS feeds from configured sources
    - Filter entries by relevance (keyword scoring)
    - Clean and normalize feed entry content
    
    Attributes:
        rss_sources: Dictionary mapping source names to feed URLs
        max_feed_search: Maximum entries to scan per source
        max_entries_per_source: Target entries to extract per source
        max_summary_words: Word limit for entry summaries
        valuable_keywords: High-quality content indicators
        noise_keywords: Low-quality content indicators
    """

    def __init__(
        self,
        profession: Profession = None,
        rss_sources: dict[str, str] | None = None,
        max_feed_search: int | None = None,
        max_entries_per_source: int | None = None,
        max_summary_words: int | None = None,
        valuable_keywords: set[str] | None = None,
        noise_keywords: set[str] | None = None,
    ) -> None:
        """Initialize RSS service with configuration (Dependency Injection).
        Args:
            profession: Profession enum for selecting RSS sources.
            rss_sources: Feed URLs by source name. Overrides profession if provided.
            max_feed_search: Max entries to scan. Defaults to config.
            max_entries_per_source: Target extracts per source. Defaults to config.
            max_summary_words: Summary word limit. Defaults to config.
            valuable_keywords: Quality indicators. Defaults to config.
            noise_keywords: Irrelevant content. Defaults to config.
        """
        if rss_sources is not None:
            self.rss_sources: dict[str, str] = rss_sources
        else:
            # Default to 'default' if no profession provided
            prof_key = profession.value if profession else "default"
            self.rss_sources: dict[str, str] = get_rss_sources_for_profession(prof_key)
            
        self.max_feed_search: int = max_feed_search or MAX_FEED_SEARCH
        self.max_entries_per_source: int = max_entries_per_source or MAX_ENTRIES_PER_SOURCE
        self.max_summary_words: int = max_summary_words or MAX_SUMMARY_WORDS
        self.valuable_keywords: set[str] = valuable_keywords or VALUABLE_KEYWORDS
        self.noise_keywords: set[str] = noise_keywords or NOISE_KEYWORDS

    async def fetch_all_feeds(self) -> str:
        """Aggregate and filter RSS feeds to extract relevant news content in a compact, line-based format.
        Raises RuntimeError if no relevant content is found.
        """
        lines: list[str] = []

        from src.utils.logger import log_info, log_warning
        log_info("\n" + "═" * 60)
        log_info("📡 SMART DATA ACQUISITION")
        log_info("═" * 60)

        for source_name, feed_url in self.rss_sources.items():
            try:
                feed: Any = feedparser.parse(feed_url)
                if not feed.entries:
                    continue

                relevant_entries: list[Any] = await self._filter_feed_entries(
                    feed.entries,
                    self.max_feed_search,
                    self.max_entries_per_source
                )

                log_info(f"✅ {source_name}: Found {len(relevant_entries)} relevant items")

                for entry in relevant_entries:
                    title = getattr(entry, 'title', '').strip()
                    link = getattr(entry, 'link', '').strip()
                    if not title or not link:
                        continue
                    # Compact line: Title - Link
                    lines.append(f"{title} - {link}")

            except Exception as e:
                log_warning(f"⚠️ Error fetching {source_name}: {e}")

        if not lines:
            raise RuntimeError("No relevant RSS content found. Pipeline execution halted.")

        return '\n'.join(lines)

    async def _filter_feed_entries(
        self,
        feed_entries: list[Any],
        max_search: int,
        max_extract: int
    ) -> list[Any]:
        """Filter RSS feed entries by relevance using keyword scoring.
        
        Implements a quality gate:
        1. Excludes entries with noise keywords
        2. Scores entries based on valuable keywords in title and summary
        3. Fills remaining quota with non-noise entries if needed
        
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
            summary_clean: str = clean_html(summary_raw).lower()

            # Reject noise entries
            if any(noise in title_lower for noise in self.noise_keywords):
                continue

            # Score by valuable keywords
            score: int = sum(
                1 for word in self.valuable_keywords
                if word in title_lower or word in summary_clean
            )

            # Selection logic: take scored entries, or fill gaps with non-noise
            is_at_tail_of_search: bool = feed_entries.index(entry) > (max_search * 0.7)
            if score >= 1 or (len(relevant_entries) < max_extract and is_at_tail_of_search):
                relevant_entries.append(entry)

        return relevant_entries
