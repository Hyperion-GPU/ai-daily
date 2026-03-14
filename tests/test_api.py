from src.server import api


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
