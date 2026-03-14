import json
import logging
from datetime import datetime, timedelta, timezone

from src.fetcher import FeedFetcher


def make_fetcher():
    fetcher = FeedFetcher.__new__(FeedFetcher)
    fetcher.config = {}
    fetcher.logger = logging.getLogger("test-fetcher")
    fetcher.time_window = 48
    fetcher.seen_url_retention_days = 7
    fetcher.seen_urls = {}
    fetcher.fetch_full_text_enabled = True
    fetcher.full_text_max_chars = 2000
    fetcher._full_text_warning_logged = False
    return fetcher


def test_is_within_time_window_handles_common_cases():
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)

    assert fetcher.is_within_time_window((now - timedelta(hours=2)).isoformat()) is True
    assert fetcher.is_within_time_window((now - timedelta(hours=72)).isoformat()) is False
    assert fetcher.is_within_time_window("") is True
    assert fetcher.is_within_time_window("not-a-date") is False


def test_apply_arxiv_prefilter_respects_flags_and_keywords():
    fetcher = make_fetcher()

    assert fetcher.apply_arxiv_prefilter({"pre_filter": False}, "Agent paper", "") is True
    assert fetcher.apply_arxiv_prefilter({"pre_filter": True, "keywords": "agent|llm"}, "Agent paper", "") is True
    assert fetcher.apply_arxiv_prefilter({"pre_filter": True, "keywords": "agent|llm"}, "Vision paper", "") is False


def test_prune_seen_urls_removes_expired_and_bad_values():
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)

    pruned = fetcher._prune_seen_urls(
        {
            "https://keep": (now - timedelta(days=1)).isoformat(),
            "https://drop": (now - timedelta(days=10)).isoformat(),
            "https://bad": "oops",
        }
    )

    assert list(pruned.keys()) == ["https://keep"]


def test_load_state_migrates_legacy_list(tmp_path):
    fetcher = make_fetcher()
    fetcher.state_file = tmp_path / "state.json"
    fetcher.state_file.write_text(
        json.dumps({"seen_urls": ["https://example.com/a", "https://example.com/b"]}),
        encoding="utf-8",
    )

    fetcher.load_state()

    assert set(fetcher.seen_urls.keys()) == {"https://example.com/a", "https://example.com/b"}
    assert all(value for value in fetcher.seen_urls.values())
