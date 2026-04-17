import json
from datetime import datetime

import pytest

import src.github.fetcher as fetcher_module
from src.github.fetcher import GitHubRateLimitExceeded, GitHubTrendingFetcher


def make_config(tmp_path):
    return {
        "timezone": "Asia/Shanghai",
        "outputs": {"output_dir": str(tmp_path)},
        "github_trending": {
            "enabled": True,
            "token_env": "GITHUB_TOKEN",
            "min_stars": 100,
            "max_projects_per_day": 10,
            "per_topic_limit": 50,
            "topics": ["llm", "agent"],
            "category_map": {
                "llm": ["llm", "large-language-model"],
                "agent": ["ai-agent", "agent"],
                "general": ["artificial-intelligence"],
            },
        },
    }


def write_snapshot(tmp_path, date_str, projects):
    github_dir = tmp_path / "github"
    github_dir.mkdir(exist_ok=True)
    payload = {
        "date": date_str,
        "generated_at": f"{date_str}T10:00:00+08:00",
        "stats": {
            "total": len(projects),
            "by_category": {},
            "by_language": {},
        },
        "projects": projects,
    }
    (github_dir / f"trending-{date_str}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.anyio
async def test_github_fetcher_computes_trends_from_previous_snapshots(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    write_snapshot(
        tmp_path,
        "2026-03-15",
        [
            {
                "id": "acme/llm-kit",
                "full_name": "acme/llm-kit",
                "stars": 1000,
                "category": "llm",
            }
        ],
    )
    write_snapshot(
        tmp_path,
        "2026-03-09",
        [
            {
                "id": "acme/llm-kit",
                "full_name": "acme/llm-kit",
                "stars": 400,
                "category": "llm",
            }
        ],
    )
    fetcher = GitHubTrendingFetcher(config)
    monkeypatch.setattr(fetcher_module, "get_github_token", lambda config: "ghs_test")

    async def fake_search_topic(client, topic):
        if topic == "llm":
            return [
                {
                    "id": "acme/llm-kit",
                    "full_name": "acme/llm-kit",
                    "description": "LLM toolkit",
                    "description_zh": None,
                    "html_url": "https://github.com/acme/llm-kit",
                    "homepage": None,
                    "stars": 1205,
                    "forks": 50,
                    "open_issues": 2,
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
                }
            ]
        return []

    monkeypatch.setattr(fetcher, "_search_topic", fake_search_topic)

    result = await fetcher.run(now=datetime.fromisoformat("2026-03-16T10:00:00+08:00"))

    assert result["outcome"] == "success"
    project = result["snapshot"]["projects"][0]
    assert project["stars_today"] == 205
    assert project["stars_weekly"] == 805
    assert project["trend"] == "hot"


@pytest.mark.anyio
async def test_github_fetcher_merges_existing_same_day_snapshot(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    write_snapshot(
        tmp_path,
        "2026-03-16",
        [
            {
                "id": "acme/existing",
                "full_name": "acme/existing",
                "description": "Existing",
                "description_zh": "已有",
                "html_url": "https://github.com/acme/existing",
                "homepage": None,
                "stars": 999,
                "forks": 10,
                "open_issues": 1,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
                "pushed_at": "2026-03-15T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "User",
                "license": "MIT",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            }
        ],
    )
    fetcher = GitHubTrendingFetcher(config)
    monkeypatch.setattr(fetcher_module, "get_github_token", lambda config: "ghs_test")

    async def fake_search_topic(client, topic):
        return [
            {
                "id": "acme/new-project",
                "full_name": "acme/new-project",
                "description": "New",
                "description_zh": None,
                "html_url": "https://github.com/acme/new-project",
                "homepage": None,
                "stars": 100,
                "forks": 5,
                "open_issues": 0,
                "language": "TypeScript",
                "topics": ["agent"],
                "category": "agent",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-16T10:00:00Z",
                "pushed_at": "2026-03-16T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "Organization",
                "license": "Apache-2.0",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            }
        ]

    monkeypatch.setattr(fetcher, "_search_topic", fake_search_topic)

    result = await fetcher.run(now=datetime.fromisoformat("2026-03-16T12:00:00+08:00"))

    ids = {project["id"] for project in result["snapshot"]["projects"]}
    assert ids == {"acme/existing", "acme/new-project"}
    existing = next(project for project in result["snapshot"]["projects"] if project["id"] == "acme/existing")
    assert existing["description_zh"] == "已有"


@pytest.mark.anyio
async def test_github_fetcher_rate_limit_keeps_official_snapshot_and_writes_partial(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    original_payload = write_snapshot(
        tmp_path,
        "2026-03-16",
        [
            {
                "id": "acme/existing",
                "full_name": "acme/existing",
                "description": "Existing",
                "description_zh": "已有",
                "html_url": "https://github.com/acme/existing",
                "homepage": None,
                "stars": 999,
                "forks": 10,
                "open_issues": 1,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
                "pushed_at": "2026-03-15T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "User",
                "license": "MIT",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            }
        ],
    )
    official_path = tmp_path / "github" / "trending-2026-03-16.json"
    before_text = official_path.read_text(encoding="utf-8")
    fetcher = GitHubTrendingFetcher(config)
    monkeypatch.setattr(fetcher_module, "get_github_token", lambda config: "ghs_test")

    calls = {"count": 0}

    async def fake_search_topic(client, topic):
        calls["count"] += 1
        if calls["count"] == 1:
            return [
                {
                    "id": "acme/partial",
                    "full_name": "acme/partial",
                    "description": "Partial",
                    "description_zh": None,
                    "html_url": "https://github.com/acme/partial",
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
                    "stars_today": None,
                    "stars_weekly": None,
                    "trend": None,
                }
            ]
        raise GitHubRateLimitExceeded("rate limit exceeded")

    monkeypatch.setattr(fetcher, "_search_topic", fake_search_topic)

    result = await fetcher.run(now=datetime.fromisoformat("2026-03-16T10:00:00+08:00"))

    partial_path = tmp_path / "github" / "trending-2026-03-16.partial.json"
    assert result == {
        "outcome": "degraded",
        "reason": "rate_limit",
        "snapshot": None,
        "partial_path": str(partial_path),
    }
    assert official_path.read_text(encoding="utf-8") == before_text
    assert read_json(official_path) == original_payload
    assert partial_path.exists()
    partial_payload = read_json(partial_path)
    assert partial_payload["outcome"] == "degraded"
    assert partial_payload["reason"] == "rate_limit"
    assert [project["id"] for project in partial_payload["projects"]] == ["acme/partial"]


@pytest.mark.anyio
async def test_github_fetcher_missing_token_returns_degraded_without_anonymous_fetch(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    fetcher = GitHubTrendingFetcher(config)
    monkeypatch.setattr(fetcher_module, "get_github_token", lambda config: None)

    called = {"count": 0}

    async def fake_search_topic(client, topic):
        called["count"] += 1
        return []

    monkeypatch.setattr(fetcher, "_search_topic", fake_search_topic)

    result = await fetcher.run(now=datetime.fromisoformat("2026-03-16T10:00:00+08:00"))

    official_path = tmp_path / "github" / "trending-2026-03-16.json"
    partial_path = tmp_path / "github" / "trending-2026-03-16.partial.json"
    assert result == {
        "outcome": "degraded",
        "reason": "missing_token",
        "snapshot": None,
        "partial_path": str(partial_path),
    }
    assert called["count"] == 0
    assert not official_path.exists()
    assert partial_path.exists()
    partial_payload = read_json(partial_path)
    assert partial_payload["reason"] == "missing_token"
    assert partial_payload["projects"] == []


@pytest.mark.anyio
async def test_github_fetcher_success_replaces_partial_with_official_snapshot(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    write_snapshot(
        tmp_path,
        "2026-03-16",
        [
            {
                "id": "acme/existing",
                "full_name": "acme/existing",
                "description": "Existing",
                "description_zh": "已有",
                "html_url": "https://github.com/acme/existing",
                "homepage": None,
                "stars": 999,
                "forks": 10,
                "open_issues": 1,
                "language": "Python",
                "topics": ["llm"],
                "category": "llm",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-03-15T10:00:00Z",
                "pushed_at": "2026-03-15T10:00:00Z",
                "owner_avatar": None,
                "owner_type": "User",
                "license": "MIT",
                "stars_today": None,
                "stars_weekly": None,
                "trend": None,
            }
        ],
    )
    partial_path = tmp_path / "github" / "trending-2026-03-16.partial.json"
    partial_path.write_text(
        json.dumps({"outcome": "degraded", "reason": "rate_limit", "projects": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fetcher = GitHubTrendingFetcher(config)
    monkeypatch.setattr(fetcher_module, "get_github_token", lambda config: "ghs_test")

    async def fake_search_topic(client, topic):
        if topic == "llm":
            return [
                {
                    "id": "acme/new-project",
                    "full_name": "acme/new-project",
                    "description": "New",
                    "description_zh": None,
                    "html_url": "https://github.com/acme/new-project",
                    "homepage": None,
                    "stars": 100,
                    "forks": 5,
                    "open_issues": 0,
                    "language": "TypeScript",
                    "topics": ["agent"],
                    "category": "agent",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-03-16T10:00:00Z",
                    "pushed_at": "2026-03-16T10:00:00Z",
                    "owner_avatar": None,
                    "owner_type": "Organization",
                    "license": "Apache-2.0",
                    "stars_today": None,
                    "stars_weekly": None,
                    "trend": None,
                }
            ]
        return []

    monkeypatch.setattr(fetcher, "_search_topic", fake_search_topic)

    result = await fetcher.run(now=datetime.fromisoformat("2026-03-16T12:00:00+08:00"))

    official_path = tmp_path / "github" / "trending-2026-03-16.json"
    assert result["outcome"] == "success"
    assert result["reason"] is None
    assert result["partial_path"] is None
    assert partial_path.exists() is False
    official_payload = read_json(official_path)
    ids = {project["id"] for project in official_payload["projects"]}
    assert ids == {"acme/existing", "acme/new-project"}
    assert result["snapshot"] == official_payload
