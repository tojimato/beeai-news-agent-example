"""Data processing and transformation pipeline.

This module implements a single-responsibility service for cleaning, validating,
and enriching raw feed data before it enters the LLM pipeline.
"""

from dataclasses import dataclass
from typing import Optional

from src.utils.text_processing import clean_html


@dataclass
class ProcessedEntry:
    """Represents a cleaned and validated feed entry.
    
    Attributes:
        title: Entry title (cleaned).
        content: Entry content/summary (cleaned and normalized).
        source: Source name for traceability.
        original_title: Original title before processing (for reference).
    """

    title: str
    content: str
    source: str
    original_title: str | None = None

    def to_markdown(self) -> str:
        """Convert entry to Markdown format for report inclusion.
        
        Returns:
            Markdown-formatted representation of the entry.
        """
        return f"**{self.title}**\n\n{self.content}\n\n*Source: {self.source}*\n"


class DataProcessor:
    """Service for cleaning, validating, and enriching pipeline data.
    
    Responsibility:
    - Validate incoming raw data
    - Clean and normalize text
    - Enrich entries with metadata
    - Transform data into structured formats
    
    NOT responsible for:
    - Fetching data (RSSService)
    - LLM processing (LLMService)
    """

    @staticmethod
    def validate_entry(title: str | None, content: str | None) -> bool:
        """Validate that an entry has minimum required content.
        
        Args:
            title: Entry title to validate.
            content: Entry content to validate.
        
        Returns:
            True if entry meets minimum quality criteria.
        """
        if not title or not content:
            return False
        
        title_clean = title.strip()
        content_clean = content.strip()
        
        # Require at least 5 characters in both title and content
        return len(title_clean) >= 5 and len(content_clean) >= 10

    @staticmethod
    def process_entry(
        title: str,
        content: str,
        source: str
    ) -> Optional[ProcessedEntry]:
        """Process and validate a single feed entry.
        
        Args:
            title: Raw entry title.
            content: Raw entry content/summary.
            source: Source name for metadata.
        
        Returns:
            ProcessedEntry if valid, None if fails validation.
        """
        if not DataProcessor.validate_entry(title, content):
            return None
        
        # Clean HTML and normalize whitespace
        clean_title: str = clean_html(title).strip()
        clean_content: str = clean_html(content).strip()
        
        # Remove excessive line breaks
        clean_content = clean_content.replace('\n\n', '\n').strip()
        
        return ProcessedEntry(
            title=clean_title,
            content=clean_content,
            source=source,
            original_title=title
        )

    @staticmethod
    def batch_process_entries(
        entries: list[dict[str, str]],
        source: str = "Unknown"
    ) -> list[ProcessedEntry]:
        """Process multiple entries, filtering invalid ones.
        
        Args:
            entries: List of dictionaries with 'title' and 'content' keys.
            source: Source name to assign to all entries.
        
        Returns:
            List of valid ProcessedEntry objects.
        """
        processed: list[ProcessedEntry] = []
        
        for entry in entries:
            title: str | None = entry.get('title')
            content: str | None = entry.get('content')
            
            processed_entry: Optional[ProcessedEntry] = DataProcessor.process_entry(
                title or "",
                content or "",
                source
            )
            
            if processed_entry:
                processed.append(processed_entry)
        
        return processed

    @staticmethod
    def format_aggregated_content(
        processed_entries: list[ProcessedEntry],
        group_by_source: bool = True
    ) -> str:
        """Format processed entries into aggregated content string.
        
        Args:
            processed_entries: List of processed entries.
            group_by_source: If True, group entries by source in output.
        
        Returns:
            Formatted string ready for LLM input.
        """
        if not processed_entries:
            return ""
        
        if group_by_source:
            return DataProcessor._format_grouped_by_source(processed_entries)
        else:
            return DataProcessor._format_flat(processed_entries)

    @staticmethod
    def _format_grouped_by_source(
        processed_entries: list[ProcessedEntry]
    ) -> str:
        """Format entries grouped by source.
        
        Args:
            processed_entries: List of processed entries.
        
        Returns:
            Formatted string grouped by source.
        """
        sources: dict[str, list[ProcessedEntry]] = {}
        
        # Group by source
        for entry in processed_entries:
            if entry.source not in sources:
                sources[entry.source] = []
            sources[entry.source].append(entry)
        
        # Format grouped output
        output: str = ""
        for source, entries in sorted(sources.items()):
            output += f"\n--- SOURCE: {source} ---\n"
            for entry in entries:
                output += f"TITLE: {entry.title}\nCONTENT: {entry.content}\n\n"
        
        return output

    @staticmethod
    def _format_flat(
        processed_entries: list[ProcessedEntry]
    ) -> str:
        """Format entries in flat structure (no grouping).
        
        Args:
            processed_entries: List of processed entries.
        
        Returns:
            Formatted flat string.
        """
        output: str = ""
        for entry in processed_entries:
            output += f"[{entry.source}] {entry.title}\n{entry.content}\n\n"
        return output

    @staticmethod
    def dedup_entries(
        processed_entries: list[ProcessedEntry]
    ) -> list[ProcessedEntry]:
        """Remove duplicate entries based on title similarity.
        
        Args:
            processed_entries: List of entries to deduplicate.
        
        Returns:
            List of unique entries.
        """
        seen_titles: set[str] = set()
        unique_entries: list[ProcessedEntry] = []
        
        for entry in processed_entries:
            # Normalize title for comparison
            title_normalized: str = entry.title.lower().strip()
            
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_entries.append(entry)
        
        return unique_entries

    @staticmethod
    def enrich_entry_metadata(
        entry: ProcessedEntry,
        **kwargs: str
    ) -> ProcessedEntry:
        """Add metadata to an entry (extensible for future use).
        
        Args:
            entry: Entry to enrich.
            **kwargs: Additional metadata key-value pairs.
        
        Returns:
            Entry (currently returns as-is, structure ready for expansion).
        """
        # Placeholder for metadata enrichment
        # Future: add sentiment, category, confidence scores, etc.
        return entry
