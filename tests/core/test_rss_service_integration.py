import pytest
from src.core.rss_service import RSSService
from src.config.professions import Profession

@pytest.mark.asyncio
async def test_fetch_all_feeds_real_sources():
    service = RSSService(profession=Profession.SOLO_DEVELOPER)
    result = await service.fetch_all_feeds()
    print("\n--- Integration Test Output ---\n" + result)
    # Check that at least one line matches the new format: Title - Link (no source prefix)
    lines = [line for line in result.split("\n") if line.strip()]
    assert lines, "No output lines found."
    found_valid = False
    for line in lines:
        if " - http" in line:
            found_valid = True
            break
    assert found_valid, "No line in output matches the expected 'Title - Link' format."
