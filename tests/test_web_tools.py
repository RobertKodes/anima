"""Web tool tests."""

from __future__ import annotations

from anima.tools.web import extract_url, is_safe_url


def test_extract_url() -> None:
    assert extract_url("fetch https://example.com please") == "https://example.com"


def test_blocks_localhost() -> None:
    ok, reason = is_safe_url("http://127.0.0.1/test")
    assert not ok
    assert "local" in reason.lower() or "blocked" in reason.lower()


def test_allows_public_https() -> None:
    ok, _ = is_safe_url("https://example.com")
    assert ok
