"""Text processing and data cleaning utilities.

This module provides helper functions for text normalization, HTML stripping,
and data validation used across the pipeline.
"""

import re
from typing import Optional


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


def truncate_text(text: str, word_limit: int) -> str:
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
