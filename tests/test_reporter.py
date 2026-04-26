import json
from datetime import datetime, timezone

from src import reporter


GENERATED_AT = datetime(2026, 3, 14, 8, 0, tzinfo=timezone.utc)


def test_generate_report_writes_json_and_markdown(tmp_path):
    config = {
        "timezone": "UTC",
        "outputs": {
            "output_dir": str(tmp_path),
            "report_filename": "{date}.md",
        },
    }
    articles = [
        {
            "title": "Important release",
            "url": "https://example.com/important",
            "published": "2026-03-14T09:00:00+00:00",
            "source_name": "Example",
            "source_category": "official",
            "summary_zh": "A major release shipped.",
            "tags": ["release", "models"],
            "importance": 5,
        },
        {
            "title": "Minor update",
            "url": "https://example.com/minor",
            "published": "2026-03-14T08:00:00+00:00",
            "source_name": "Example",
            "source_category": "news",
            "summary_zh": "A smaller follow-up update.",
            "tags": ["news"],
            "importance": 2,
        },
    ]

    md_path = reporter.generate_report(articles, config, generated_at=GENERATED_AT)
    json_path = tmp_path / "2026-03-14.json"

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    index_payload = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))

    assert md_path == tmp_path / "2026-03-14.md"
    assert payload["stats"]["total"] == 2
    assert payload["stats"]["by_category"] == {"official": 1, "news": 1}
    assert payload["stats"]["by_tag"] == {"release": 1, "models": 1, "news": 1}
    assert payload["articles"][0]["id"] == reporter._article_id("https://example.com/important")
    assert "id" not in articles[0]
    assert index_payload == [
        {
            "date": "2026-03-14",
            "total": 2,
            "by_category": {"official": 1, "news": 1},
        }
    ]
    assert "## Highlights" in markdown
    assert "## More Updates" in markdown
    assert "Important release" in markdown


def test_generate_report_handles_empty_article_list(tmp_path):
    config = {
        "timezone": "UTC",
        "outputs": {
            "output_dir": str(tmp_path),
            "report_filename": "{date}.md",
        },
    }

    md_path = reporter.generate_report([], config, generated_at=GENERATED_AT)
    markdown = md_path.read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "2026-03-14.json").read_text(encoding="utf-8"))

    assert payload["stats"]["total"] == 0
    assert payload["articles"] == []
    assert "_No new high-value AI updates today._" in markdown


def test_generate_report_escapes_markdown_and_rejects_unsafe_links(tmp_path):
    config = {
        "timezone": "UTC",
        "outputs": {
            "output_dir": str(tmp_path),
            "report_filename": "{date}.md",
        },
    }
    articles = [
        {
            "title": "Title ](spoof)\nNext <img src=x>",
            "url": "javascript:alert(1)",
            "published": "2026-03-14T09:00:00+00:00",
            "source_name": "Source [beta] <b>team</b>",
            "source_category": "news",
            "summary_zh": "Summary [x]\nline two <script>alert(1)</script> & more",
            "tags": ["tag`x"],
            "importance": 5,
        }
    ]

    md_path = reporter.generate_report(articles, config, generated_at=GENERATED_AT)
    markdown = md_path.read_text(encoding="utf-8")

    assert "](javascript:alert(1))" not in markdown
    assert "<img" not in markdown
    assert "<script>" not in markdown
    assert "&lt;img src=x&gt;" in markdown
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in markdown
    assert "### Title \\](spoof) Next &lt;img src=x&gt;" in markdown
    assert "Source \\[beta\\] &lt;b&gt;team&lt;/b&gt;" in markdown
    assert "`tag'x`" in markdown
    assert "Summary \\[x\\] line two" in markdown


def test_generate_report_updates_existing_index_entry(tmp_path):
    config = {
        "timezone": "UTC",
        "outputs": {
            "output_dir": str(tmp_path),
            "report_filename": "{date}.md",
        },
    }
    (tmp_path / "index.json").write_text(
        json.dumps(
            [
                {"date": "2026-03-13", "total": 1, "by_category": {"news": 1}},
                {"date": "2026-03-14", "total": 9, "by_category": {"official": 9}},
            ]
        ),
        encoding="utf-8",
    )

    reporter.generate_report([], config, generated_at=GENERATED_AT)
    index_payload = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))

    assert index_payload == [
        {"date": "2026-03-14", "total": 0, "by_category": {}},
        {"date": "2026-03-13", "total": 1, "by_category": {"news": 1}},
    ]
