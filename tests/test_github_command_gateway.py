from __future__ import annotations

import pytest

from src.desktop.tasks import GithubCommandGateway


def _sample_snapshot(date: str = "2026-04-15") -> dict:
    return {
        "date": date,
        "generated_at": f"{date}T10:00:00+08:00",
        "stats": {
            "total": 1,
            "by_category": {"llm": 1},
            "by_language": {"Python": 1},
        },
        "projects": [
            {
                "id": "acme/alpha",
                "full_name": "acme/alpha",
                "description": "Alpha helper",
                "description_zh": "Alpha 助手",
                "html_url": "https://github.com/acme/alpha",
                "homepage": None,
                "stars": 1200,
                "forks": 32,
                "open_issues": 4,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-04-15T08:00:00Z",
                "pushed_at": "2026-04-15T08:00:00Z",
                "owner_avatar": "",
                "owner_type": "Organization",
                "license": "MIT",
                "stars_today": 25,
                "stars_weekly": 180,
                "trend": "rising",
            }
        ],
    }


class FakeServices:
    def __init__(self) -> None:
        self.latest_kwargs: dict | None = None
        self.by_date_call: tuple[str, dict] | None = None
        self.fetch_called = False
        self.fetch_result = {
            "outcome": "success",
            "reason": None,
            "snapshot": _sample_snapshot(),
            "partial_path": None,
        }

    def get_github_dates(self) -> dict:
        return {"dates": ["2026-04-15", "2026-04-14"], "latest": "2026-04-15"}

    def get_latest_github_trending(self, **kwargs) -> dict | None:
        self.latest_kwargs = kwargs
        return _sample_snapshot()

    def get_github_trending_by_date(self, date: str, **kwargs) -> dict | None:
        self.by_date_call = (date, kwargs)
        return _sample_snapshot(date)

    async def run_github_fetch_async(self, progress_callback=None) -> dict:
        self.fetch_called = True
        if progress_callback is not None:
            progress_callback({"stage": "searching", "message": "Searching topic: llm"})
        return self.fetch_result


def test_github_gateway_lists_dates_as_qml_friendly_items() -> None:
    services = FakeServices()
    gateway = GithubCommandGateway(lambda: services)

    payload = gateway.list_dates()

    assert payload["latest"] == "2026-04-15"
    assert payload["dates"][0] == {
        "date": "2026-04-15",
        "label": "2026-04-15",
        "isLatest": True,
        "projectCount": None,
        "generatedAt": None,
    }


def test_github_gateway_loads_latest_snapshot_and_normalizes_filters() -> None:
    services = FakeServices()
    gateway = GithubCommandGateway(lambda: services)

    payload = gateway.load_snapshot(
        None,
        {
            "categoryFilter": "llm",
            "selectedLanguages": ["Python"],
            "minStars": 500,
            "sortKey": "stars_weekly",
            "searchQuery": "alpha",
            "trendFilter": "rising",
        },
    )

    assert services.latest_kwargs == {
        "category": "llm",
        "language": ["Python"],
        "min_stars": 500,
        "sort": "stars_weekly",
        "q": "alpha",
        "trend": "rising",
    }
    assert payload is not None
    assert payload["generatedAt"] == "2026-04-15T10:00:00+08:00"
    assert payload["stats"]["byLanguage"] == {"Python": 1}
    assert payload["projects"][0]["fullName"] == "acme/alpha"
    assert payload["projects"][0]["htmlUrl"] == "https://github.com/acme/alpha"


def test_github_gateway_loads_specific_date_snapshot() -> None:
    services = FakeServices()
    gateway = GithubCommandGateway(lambda: services)

    payload = gateway.load_snapshot("2026-04-14", {"selectedLanguages": "Python"})

    assert services.by_date_call == (
        "2026-04-14",
        {
            "category": None,
            "language": ["Python"],
            "min_stars": 0,
            "sort": "stars",
            "q": None,
            "trend": None,
        },
    )
    assert payload is not None
    assert payload["date"] == "2026-04-14"


@pytest.mark.anyio
async def test_github_gateway_runs_fetch_and_serializes_success_result() -> None:
    services = FakeServices()
    gateway = GithubCommandGateway(lambda: services)
    progress_events: list[dict] = []

    payload = await gateway.run_fetch(progress_events.append)

    assert services.fetch_called is True
    assert progress_events == [{"stage": "searching", "message": "Searching topic: llm"}]
    assert payload["outcome"] == "success"
    assert payload["reason"] is None
    assert payload["partialPath"] is None
    assert payload["snapshot"]["projects"][0]["starsToday"] == 25


@pytest.mark.anyio
async def test_github_gateway_runs_fetch_and_serializes_degraded_result() -> None:
    services = FakeServices()
    services.fetch_result = {
        "outcome": "degraded",
        "reason": "rate_limit",
        "snapshot": None,
        "partial_path": "/tmp/trending-2026-04-15.partial.json",
    }
    gateway = GithubCommandGateway(lambda: services)

    payload = await gateway.run_fetch()

    assert payload == {
        "outcome": "degraded",
        "reason": "rate_limit",
        "snapshot": None,
        "partialPath": "/tmp/trending-2026-04-15.partial.json",
    }
