import json
from datetime import datetime

import pytest

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

    project = result["projects"][0]
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

    ids = {project["id"] for project in result["projects"]}
    assert ids == {"acme/existing", "acme/new-project"}
    existing = next(project for project in result["projects"] if project["id"] == "acme/existing")
    assert existing["description_zh"] == "已有"


@pytest.mark.anyio
async def test_github_fetcher_saves_partial_snapshot_when_rate_limited(tmp_path, monkeypatch):
    config = make_config(tmp_path)
    fetcher = GitHubTrendingFetcher(config)

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

    assert [project["id"] for project in result["projects"]] == ["acme/partial"]
    snapshot_path = tmp_path / "github" / "trending-2026-03-16.json"
    assert snapshot_path.exists()
