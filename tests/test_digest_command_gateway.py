from __future__ import annotations

import copy

import pytest

from src.desktop.tasks.digest_command_gateway import DigestCommandGateway


def _article(
    article_id: str,
    *,
    title: str,
    source_category: str,
    source_name: str,
    tags: list[str],
    importance: int,
    published: str,
) -> dict:
    return {
        "id": article_id,
        "title": title,
        "url": f"https://example.com/{article_id}",
        "published": published,
        "source_name": source_name,
        "source_category": source_category,
        "summary_zh": f"{title} summary",
        "tags": tags,
        "importance": importance,
    }


def _snapshot(date: str = "2026-04-15") -> dict:
    return {
        "date": date,
        "generated_at": f"{date}T10:00:00+08:00",
        "stats": {
            "total": 2,
            "by_category": {"news": 1, "official": 1},
            "by_tag": {"llm": 2, "agents": 1},
        },
        "articles": [
            _article(
                "alpha",
                title="Alpha",
                source_category="news",
                source_name="Alpha News",
                tags=["llm", "agents"],
                importance=5,
                published="2026-04-15T09:00:00+08:00",
            ),
            _article(
                "beta",
                title="Beta",
                source_category="official",
                source_name="Beta Labs",
                tags=["llm"],
                importance=4,
                published="2026-04-15T08:00:00+08:00",
            ),
        ],
    }


class FakeServices:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.fetch_called = False
        self.fetch_result: dict = {"result": "success", "article_count": 2}

    def get_dates(self) -> dict:
        return {
            "dates": [
                {"date": "2026-04-15", "total": 2, "by_category": {"news": 1, "official": 1}},
                {"date": "2026-04-14", "total": 1, "by_category": {"news": 1}},
            ],
            "latest": "2026-04-15",
        }

    def get_digest(self, date: str, **kwargs) -> dict | None:
        self.calls.append((date, kwargs))
        return _snapshot(date)

    async def run_pipeline_async(self, progress_callback=None) -> dict:
        self.fetch_called = True
        if progress_callback is not None:
            progress_callback({"stage": "fetching", "message": "Collected feeds"})
        return copy.deepcopy(self.fetch_result)


def test_digest_gateway_lists_dates_as_qml_friendly_items() -> None:
    services = FakeServices()
    gateway = DigestCommandGateway(lambda: services)

    payload = gateway.list_dates()

    assert payload == {
        "latest": "2026-04-15",
        "dates": [
            {
                "date": "2026-04-15",
                "label": "2026-04-15",
                "articleCount": 2,
                "isLatest": True,
            },
            {
                "date": "2026-04-14",
                "label": "2026-04-14",
                "articleCount": 1,
                "isLatest": False,
            },
        ],
    }


def test_digest_gateway_loads_latest_snapshot_and_normalizes_filters() -> None:
    services = FakeServices()
    gateway = DigestCommandGateway(lambda: services)

    payload = gateway.load_snapshot(
        None,
        {
            "selectedTags": ["llm", "agents", "llm"],
            "categoryFilter": "news",
            "minImportance": 3,
            "sortKey": "published",
            "searchQuery": "Alpha",
        },
    )

    assert services.calls == [
        (
            "2026-04-15",
            {
                "tags": ["llm", "agents"],
                "category": "news",
                "min_importance": 3,
                "sort": "published",
                "q": "Alpha",
            },
        )
    ]
    assert payload is not None
    assert payload["generatedAt"] == "2026-04-15T10:00:00+08:00"
    assert payload["stats"]["byCategory"] == {"news": 1, "official": 1}
    assert payload["stats"]["byTag"] == {"llm": 2, "agents": 1}
    assert payload["articles"][0]["sourceName"] == "Alpha News"
    assert payload["articles"][0]["sourceCategory"] == "news"
    assert payload["articles"][0]["summaryZh"] == "Alpha summary"


def test_digest_gateway_loads_specific_date_snapshot() -> None:
    services = FakeServices()
    gateway = DigestCommandGateway(lambda: services)

    payload = gateway.load_snapshot("2026-04-14", {"selectedTags": "llm"})

    assert services.calls == [
        (
            "2026-04-14",
            {
                "tags": ["llm"],
                "category": None,
                "min_importance": 1,
                "sort": "importance",
                "q": None,
            },
        )
    ]
    assert payload is not None
    assert payload["date"] == "2026-04-14"


@pytest.mark.anyio
async def test_digest_gateway_runs_fetch_and_passes_progress() -> None:
    services = FakeServices()
    gateway = DigestCommandGateway(lambda: services)
    progress_events: list[dict] = []

    payload = await gateway.run_fetch(progress_events.append)

    assert services.fetch_called is True
    assert progress_events == [{"stage": "fetching", "message": "Collected feeds"}]
    assert payload == {"result": "success", "article_count": 2, "outcome": "success"}


@pytest.mark.anyio
async def test_digest_gateway_normalizes_no_new_items_outcome() -> None:
    services = FakeServices()
    services.fetch_result = {"result": "no_new_items", "article_count": 2}
    gateway = DigestCommandGateway(lambda: services)

    payload = await gateway.run_fetch()

    assert payload == {"result": "no_new_items", "article_count": 2, "outcome": "no_new_items"}
