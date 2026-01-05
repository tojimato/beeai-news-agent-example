"""Tests for profession-aware keyword merging in settings.

These ensure `get_valuable_keywords_for_profession` merges the default
`VALUABLE_KEYWORDS` with any profession-specific overrides and accepts
both strings and Enums with a `value` attribute.
"""
from enum import Enum

from src.config import settings


def test_merges_profession_keywords() -> None:
    merged = settings.get_valuable_keywords_for_profession("interior_designer")
    assert isinstance(merged, set)
    # core default keyword
    assert "design" in merged
    # profession-specific keyword
    assert "lighting" in merged


def test_unknown_profession_returns_default_copy() -> None:
    merged = settings.get_valuable_keywords_for_profession("unknown_prof")
    assert merged == settings.VALUABLE_KEYWORDS
    # ensure it's a copy (not the identical object)
    assert merged is not settings.VALUABLE_KEYWORDS


def test_accepts_enum_profession() -> None:
    class Prof(Enum):
        DEV = "solo_developer"

    merged = settings.get_valuable_keywords_for_profession(Prof.DEV)
    assert "ai" in merged
    assert "dev" in merged
