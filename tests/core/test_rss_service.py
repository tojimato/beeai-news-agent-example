import pytest
from unittest.mock import patch, MagicMock
import asyncio

from src.core.rss_service import RSSService
from src.config.professions import Profession

@pytest.mark.asyncio
async def test_fetch_all_feeds_includes_link():
    # Mock feedparser.parse to return a fake feed with entries
    mock_entry = MagicMock()
    mock_entry.title = "AI Test News Title"
    mock_entry.link = "http://example.com/test-news"
    mock_entry.summary = "Test summary content."
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("feedparser.parse", return_value=mock_feed):
        service = RSSService(profession=Profession.SOLO_DEVELOPER, rss_sources={"TestSource": "http://fake-url.com/rss"})
        result = await service.fetch_all_feeds()

    # Check that the output matches the new format: 'Title - Link'
    assert "AI Test News Title - http://example.com/test-news" in result
    print("\n--- Test Output ---\n" + result)
