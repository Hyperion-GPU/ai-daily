import json
import logging
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src import fetcher as fetcher_module
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
    fetcher.full_text_concurrency = 5
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


def test_save_state_writes_seen_urls_payload(tmp_path):
    fetcher = make_fetcher()
    fetcher.state_file = tmp_path / "state.json"
    seen_at = datetime.now(timezone.utc).isoformat()
    fetcher.seen_urls = {"https://example.com/a": seen_at}

    fetcher.save_state()

    payload = json.loads(fetcher.state_file.read_text(encoding="utf-8"))
    assert payload == {"seen_urls": {"https://example.com/a": seen_at}}


@pytest.mark.anyio
async def test_fetch_feed_filters_seen_old_and_prefiltered_entries(monkeypatch):
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)
    fetcher.seen_urls = {"https://example.com/seen": now.isoformat()}
    fetcher._enrich_articles_with_full_text = AsyncMock()

    class FeedEntry(dict):
        __getattr__ = dict.get

    entries = [
        FeedEntry(
            link="https://example.com/fresh",
            title="Agent release",
            published=(now - timedelta(hours=2)).isoformat(),
            summary="<p>Fresh agent summary</p>",
            content=[{"value": "<div>Full content</div>"}],
        ),
        FeedEntry(
            link="https://example.com/old",
            title="Agent history",
            published=(now - timedelta(hours=80)).isoformat(),
            summary="Old item",
        ),
        FeedEntry(
            link="https://example.com/seen",
            title="Seen item",
            published=(now - timedelta(hours=1)).isoformat(),
            summary="Seen item",
        ),
        FeedEntry(
            link="https://example.com/vision",
            title="Vision release",
            published=(now - timedelta(hours=1)).isoformat(),
            summary="Not matched",
        ),
    ]

    monkeypatch.setattr(fetcher_module.feedparser, "parse", lambda _: SimpleNamespace(entries=entries))

    class FakeResponse:
        text = "<rss />"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url, timeout, follow_redirects):
            return FakeResponse()

    articles, new_urls = await fetcher.fetch_feed(
        FakeClient(),
        {
            "url": "https://example.com/feed.xml",
            "name": "Example Feed",
            "category": "news",
            "pre_filter": True,
            "keywords": "agent",
        },
    )

    assert [article.url for article in articles] == ["https://example.com/fresh"]
    assert articles[0].summary == "Fresh agent summary"
    assert articles[0].content == "Full content"
    assert new_urls == {"https://example.com/fresh"}
    fetcher._enrich_articles_with_full_text.assert_awaited_once()


@pytest.mark.anyio
async def test_fetch_feed_enriches_each_eligible_article_once(monkeypatch):
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)
    calls: list[str] = []

    class FeedEntry(dict):
        __getattr__ = dict.get

    entries = [
        FeedEntry(
            link=f"https://example.com/article-{index}",
            title=f"Article {index}",
            published=(now - timedelta(hours=1)).isoformat(),
            summary=f"Summary {index}",
        )
        for index in range(3)
    ]

    monkeypatch.setattr(fetcher_module.feedparser, "parse", lambda _: SimpleNamespace(entries=entries))

    async def fake_fetch_full_text(client, url):
        calls.append(url)
        return f"Full text for {url}"

    fetcher.fetch_full_text = fake_fetch_full_text

    class FakeResponse:
        text = "<rss />"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url, timeout, follow_redirects):
            return FakeResponse()

    articles, new_urls = await fetcher.fetch_feed(
        FakeClient(),
        {
            "url": "https://example.com/feed.xml",
            "name": "Example Feed",
            "category": "news",
        },
    )

    assert [article.url for article in articles] == calls
    assert calls == [f"https://example.com/article-{index}" for index in range(3)]
    assert new_urls == set(calls)
    assert [article.content for article in articles] == [
        f"Full text for https://example.com/article-{index}" for index in range(3)
    ]


@pytest.mark.anyio
@pytest.mark.parametrize("category", ["news", "official", "community"])
async def test_fetch_feed_calls_enrichment_once_after_collecting_eligible_articles(monkeypatch, category):
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)
    fetcher._enrich_articles_with_full_text = AsyncMock()

    class FeedEntry(dict):
        __getattr__ = dict.get

    entries = [
        FeedEntry(
            link=f"https://example.com/{category}-{index}",
            title=f"{category} article {index}",
            published=(now - timedelta(hours=1)).isoformat(),
            summary=f"Summary {index}",
        )
        for index in range(3)
    ]

    monkeypatch.setattr(fetcher_module.feedparser, "parse", lambda _: SimpleNamespace(entries=entries))

    class FakeResponse:
        text = "<rss />"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url, timeout, follow_redirects):
            return FakeResponse()

    articles, _ = await fetcher.fetch_feed(
        FakeClient(),
        {
            "url": "https://example.com/feed.xml",
            "name": "Example Feed",
            "category": category,
        },
    )

    fetcher._enrich_articles_with_full_text.assert_awaited_once()
    _, enriched_articles = fetcher._enrich_articles_with_full_text.await_args.args
    assert enriched_articles is articles
    assert [article.url for article in enriched_articles] == [
        f"https://example.com/{category}-{index}" for index in range(3)
    ]


@pytest.mark.anyio
async def test_fetch_feed_does_not_enrich_arxiv_articles(monkeypatch):
    fetcher = make_fetcher()
    now = datetime.now(timezone.utc)
    calls: list[str] = []

    class FeedEntry(dict):
        __getattr__ = dict.get

    entries = [
        FeedEntry(
            link="https://example.com/arxiv",
            title="Arxiv paper",
            published=(now - timedelta(hours=1)).isoformat(),
            summary="Paper summary",
        )
    ]

    monkeypatch.setattr(fetcher_module.feedparser, "parse", lambda _: SimpleNamespace(entries=entries))

    async def fake_fetch_full_text(client, url):
        calls.append(url)
        return "Full text"

    fetcher.fetch_full_text = fake_fetch_full_text

    class FakeResponse:
        text = "<rss />"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url, timeout, follow_redirects):
            return FakeResponse()

    articles, new_urls = await fetcher.fetch_feed(
        FakeClient(),
        {
            "url": "https://example.com/feed.xml",
            "name": "Arxiv Feed",
            "category": "arxiv",
        },
    )

    assert [article.url for article in articles] == ["https://example.com/arxiv"]
    assert new_urls == {"https://example.com/arxiv"}
    assert calls == []
