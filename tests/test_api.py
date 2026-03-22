import asyncio

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.server import api
from src.server.main import app


def test_get_digest_search_uses_casefold(monkeypatch):
    payload = {
        "date": "2026-03-14",
        "generated_at": "2026-03-14T08:00:00+00:00",
        "articles": [
            {
                "id": "1",
                "title": "Stra\u00dfe Models",
                "url": "https://example.com/1",
                "published": "2026-03-14T08:00:00+00:00",
                "source_name": "Example",
                "source_category": "news",
                "summary_zh": "Summary",
                "tags": ["LLMs"],
                "importance": 3,
            }
        ],
    }

    monkeypatch.setattr(api, "load_digest", lambda date: payload)

    result = api.get_digest("2026-03-14", tags=[], min_importance=1, sort="importance", q="strasse")

    assert result["stats"]["total"] == 1


def test_get_digest_sorts_published_across_timezones(monkeypatch):
    payload = {
        "date": "2026-03-14",
        "generated_at": "2026-03-14T08:00:00+00:00",
        "articles": [
            {
                "id": "older",
                "title": "Older",
                "url": "https://example.com/older",
                "published": "2026-03-14T09:00:00+08:00",
                "source_name": "Example",
                "source_category": "news",
                "summary_zh": "Summary",
                "tags": ["LLMs"],
                "importance": 5,
            },
            {
                "id": "newer",
                "title": "Newer",
                "url": "https://example.com/newer",
                "published": "2026-03-14T03:00:00Z",
                "source_name": "Example",
                "source_category": "news",
                "summary_zh": "Summary",
                "tags": ["LLMs"],
                "importance": 1,
            },
        ],
    }

    monkeypatch.setattr(api, "load_digest", lambda date: payload)

    result = api.get_digest("2026-03-14", tags=[], min_importance=1, sort="published")

    assert [article["id"] for article in result["articles"]] == ["newer", "older"]


def test_get_dates_prefers_index_for_stats(monkeypatch):
    monkeypatch.setattr(api, "list_dates", lambda: ["2026-03-14", "2026-03-13"])
    monkeypatch.setattr(
        api,
        "load_index",
        lambda: [
            {"date": "2026-03-14", "total": 3, "by_category": {"official": 2, "news": 1}},
            {"date": "2026-03-13", "total": 1, "by_category": {"arxiv": 1}},
        ],
    )
    monkeypatch.setattr(api, "load_digest", lambda date: None)

    result = api.get_dates()

    assert result == {
        "dates": [
            {"date": "2026-03-14", "total": 3, "by_category": {"official": 2, "news": 1}},
            {"date": "2026-03-13", "total": 1, "by_category": {"arxiv": 1}},
        ],
        "latest": "2026-03-14",
    }


def test_get_dates_falls_back_to_digest_when_index_missing_entry(monkeypatch):
    monkeypatch.setattr(api, "list_dates", lambda: ["2026-03-14"])
    monkeypatch.setattr(api, "load_index", lambda: [])
    monkeypatch.setattr(
        api,
        "load_digest",
        lambda date: {"stats": {"total": 5, "by_category": {"community": 5}}},
    )

    result = api.get_dates()

    assert result == {
        "dates": [{"date": "2026-03-14", "total": 5, "by_category": {"community": 5}}],
        "latest": "2026-03-14",
    }


def test_get_github_dates(monkeypatch):
    monkeypatch.setattr(api, "list_github_dates", lambda: ["2026-03-16", "2026-03-15"])

    result = api.get_github_dates()

    assert result == {
        "dates": ["2026-03-16", "2026-03-15"],
        "latest": "2026-03-16",
    }


def test_get_github_trending_filters_and_sorts(monkeypatch):
    payload = {
        "date": "2026-03-16",
        "generated_at": "2026-03-16T10:00:00+08:00",
        "projects": [
            {
                "id": "acme/a",
                "full_name": "acme/a",
                "description": "LLM helper",
                "description_zh": None,
                "html_url": "https://github.com/acme/a",
                "homepage": None,
                "stars": 1000,
                "forks": 10,
                "open_issues": 1,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
                "pushed_at": "2026-03-15T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "Organization",
                "license": "MIT",
                "stars_today": 10,
                "stars_weekly": 120,
                "trend": "rising",
            },
            {
                "id": "acme/b",
                "full_name": "acme/b",
                "description": "Agent helper",
                "description_zh": None,
                "html_url": "https://github.com/acme/b",
                "homepage": None,
                "stars": 1200,
                "forks": 8,
                "open_issues": 0,
                "language": "TypeScript",
                "topics": ["agent"],
                "category": "agent",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-16T10:00:00Z",
                "pushed_at": "2026-03-16T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "Organization",
                "license": "MIT",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            },
        ],
    }

    monkeypatch.setattr(api, "load_github_trending", lambda date: payload)

    result = api.get_github_trending_by_date(
        "2026-03-16",
        category="llm",
        language=["Python"],
        min_stars=500,
        sort="stars_weekly",
        q="helper",
        trend="rising",
    )

    assert result["stats"]["total"] == 1
    assert result["projects"][0]["id"] == "acme/a"
    assert result["stats"]["by_language"] == {"Python": 1}


def test_get_github_trending_sorts_zero_growth_before_missing_values(monkeypatch):
    payload = {
        "date": "2026-03-16",
        "generated_at": "2026-03-16T10:00:00+08:00",
        "projects": [
            {
                "id": "acme/zero",
                "full_name": "acme/zero",
                "description": "Zero",
                "description_zh": None,
                "html_url": "https://github.com/acme/zero",
                "homepage": None,
                "stars": 100,
                "forks": 1,
                "open_issues": 0,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-16T10:00:00Z",
                "pushed_at": "2026-03-16T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "Organization",
                "license": "MIT",
                "stars_today": 0,
                "stars_weekly": 0,
                "trend": "stable",
            },
            {
                "id": "acme/missing",
                "full_name": "acme/missing",
                "description": "Missing",
                "description_zh": None,
                "html_url": "https://github.com/acme/missing",
                "homepage": None,
                "stars": 101,
                "forks": 1,
                "open_issues": 0,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-16T10:00:00Z",
                "pushed_at": "2026-03-16T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "Organization",
                "license": "MIT",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            },
        ],
    }

    monkeypatch.setattr(api, "load_github_trending", lambda date: payload)

    result = api.get_github_trending_by_date("2026-03-16", language=[], min_stars=0, sort="stars_today")

    assert [project["id"] for project in result["projects"]] == ["acme/zero", "acme/missing"]


def test_get_latest_github_trending_uses_latest_snapshot(monkeypatch):
    payload = {
        "date": "2026-03-16",
        "generated_at": "2026-03-16T10:00:00+08:00",
        "projects": [],
    }
    monkeypatch.setattr(api, "list_github_dates", lambda: ["2026-03-16"])
    monkeypatch.setattr(api, "load_github_trending", lambda date: payload)

    result = api.get_latest_github_trending(language=[], min_stars=0, sort="stars")

    assert result["date"] == "2026-03-16"


def test_github_fetch_http_endpoint_accepts_post(monkeypatch):
    api._reset_github_fetch_state()

    class FakeFetcher:
        def __init__(self, config):
            self.config = config

        async def run(self, progress_callback=None):
            return {"date": "2026-03-16"}

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})
    monkeypatch.setattr(api, "GitHubTrendingFetcher", FakeFetcher)

    client = TestClient(app)
    response = client.post("/api/github/fetch")

    assert response.status_code == 200
    assert response.json() == {"status": "started"}


def test_pipeline_run_http_endpoint_accepts_post(monkeypatch):
    api._reset_pipeline_state()

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})

    async def fake_run_pipeline(config, progress_callback=None):
        return {"result": "success", "article_count": 1}

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    client = TestClient(app)
    response = client.post("/api/pipeline/run")

    assert response.status_code == 200
    assert response.json() == {"status": "started"}


def test_missing_api_route_returns_not_found():
    client = TestClient(app)
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404


def test_github_trending_date_rejects_invalid_format():
    client = TestClient(app)
    response = client.get("/api/github/trending/not-a-date")

    assert response.status_code == 422


async def _wait_for_task(task):
    await task


@pytest.mark.anyio
async def test_pipeline_run_endpoint_starts_background_task(monkeypatch):
    api._reset_pipeline_state()
    started = asyncio.Event()
    finish = asyncio.Event()

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})

    async def fake_run_pipeline(config, progress_callback=None):
        if progress_callback is not None:
            progress_callback(
                {
                    "stage": "fetching",
                    "message": "Fetching feeds",
                    "current": 0,
                    "total": None,
                }
            )
        started.set()
        await finish.wait()
        return {"result": "success", "article_count": 1}

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    result = await api.run_pipeline_endpoint()

    assert result == {"status": "started"}
    await asyncio.wait_for(started.wait(), timeout=1)
    status = api.get_pipeline_status()
    assert status["running"] is True
    assert status["progress"]["stage"] == "fetching"

    task = api._pipeline_state.task
    assert task is not None
    finish.set()
    await _wait_for_task(task)

    status = api.get_pipeline_status()
    assert status["running"] is False
    assert status["error"] is None
    assert status["last_outcome"] == "success"
    assert status["progress"]["stage"] == "fetching"


@pytest.mark.anyio
async def test_github_fetch_endpoint_starts_background_task(monkeypatch):
    api._reset_github_fetch_state()
    started = asyncio.Event()
    finish = asyncio.Event()

    class FakeFetcher:
        def __init__(self, config):
            self.config = config

        async def run(self, progress_callback=None):
            if progress_callback is not None:
                progress_callback(
                    {
                        "stage": "searching",
                        "message": "Searching topic: llm",
                        "current": 1,
                        "total": 2,
                    }
                )
            started.set()
            await finish.wait()
            return {"date": "2026-03-16"}

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})
    monkeypatch.setattr(api, "GitHubTrendingFetcher", FakeFetcher)

    result = await api.run_github_fetch_endpoint()

    assert result == {"status": "started"}
    await asyncio.wait_for(started.wait(), timeout=1)
    status = await api.get_github_fetch_status()
    assert status["running"] is True
    assert status["progress"]["stage"] == "searching"

    task = api._github_fetch_state.task
    assert task is not None
    finish.set()
    await _wait_for_task(task)

    status = await api.get_github_fetch_status()
    assert status["running"] is False
    assert status["error"] is None
    assert status["last_outcome"] == "success"


@pytest.mark.anyio
async def test_github_fetch_endpoint_rejects_concurrent_start(monkeypatch):
    api._reset_github_fetch_state()
    finish = asyncio.Event()

    class FakeFetcher:
        def __init__(self, config):
            self.config = config

        async def run(self, progress_callback=None):
            await finish.wait()
            return {"date": "2026-03-16"}

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})
    monkeypatch.setattr(api, "GitHubTrendingFetcher", FakeFetcher)

    await api.run_github_fetch_endpoint()

    with pytest.raises(HTTPException) as exc_info:
        await api.run_github_fetch_endpoint()

    assert exc_info.value.status_code == 409
    task = api._github_fetch_state.task
    assert task is not None
    finish.set()
    await _wait_for_task(task)


@pytest.mark.anyio
async def test_github_fetch_status_reports_failures(monkeypatch):
    api._reset_github_fetch_state()

    class FakeFetcher:
        def __init__(self, config):
            self.config = config

        async def run(self, progress_callback=None):
            raise RuntimeError("github failed")

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})
    monkeypatch.setattr(api, "GitHubTrendingFetcher", FakeFetcher)

    await api.run_github_fetch_endpoint()

    task = api._github_fetch_state.task
    assert task is not None
    await _wait_for_task(task)

    status = await api.get_github_fetch_status()
    assert status["running"] is False
    assert status["error"] == "github failed"
    assert status["last_outcome"] == "error"
    assert status["progress"]["stage"] == "error"


@pytest.mark.anyio
async def test_pipeline_run_endpoint_rejects_concurrent_start(monkeypatch):
    api._reset_pipeline_state()
    finish = asyncio.Event()

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})

    async def fake_run_pipeline(config, progress_callback=None):
        await finish.wait()
        return {"result": "success", "article_count": 1}

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    await api.run_pipeline_endpoint()

    with pytest.raises(HTTPException) as exc_info:
        await api.run_pipeline_endpoint()

    assert exc_info.value.status_code == 409
    task = api._pipeline_state.task
    assert task is not None
    finish.set()
    await _wait_for_task(task)


@pytest.mark.anyio
async def test_pipeline_status_reports_failures(monkeypatch):
    api._reset_pipeline_state()

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})

    async def fake_run_pipeline(config, progress_callback=None):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    await api.run_pipeline_endpoint()

    task = api._pipeline_state.task
    assert task is not None
    await _wait_for_task(task)

    status = api.get_pipeline_status()
    assert status["running"] is False
    assert status["error"] == "pipeline failed"
    assert status["last_outcome"] == "error"
    assert status["progress"]["stage"] == "error"


@pytest.mark.anyio
async def test_pipeline_status_reports_no_new_items(monkeypatch):
    api._reset_pipeline_state()

    monkeypatch.setattr(api, "load_config", lambda: {"timezone": "UTC"})

    async def fake_run_pipeline(config, progress_callback=None):
        return {"result": "no_new_items", "article_count": 3}

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    await api.run_pipeline_endpoint()

    task = api._pipeline_state.task
    assert task is not None
    await _wait_for_task(task)

    status = api.get_pipeline_status()
    assert status["running"] is False
    assert status["error"] is None
    assert status["last_outcome"] == "no_new_items"
