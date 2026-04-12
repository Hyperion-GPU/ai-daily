import json
import logging
import asyncio
from datetime import datetime, timezone

import pytest

import main
from src.fetcher import RawArticle


def test_partial_results_round_trip(tmp_path):
    partial_path = tmp_path / "2026-03-14.partial.json"
    articles = [
        {
            "title": "Cached article",
            "url": "https://example.com/a",
            "published": "2026-03-14T08:00:00+00:00",
            "source_name": "Example",
            "source_category": "news",
            "summary_zh": "summary",
            "tags": ["AI"],
            "importance": 4,
        }
    ]

    main._write_partial_results(partial_path, "2026-03-14", articles)
    recovered = main._load_partial_results(partial_path, logging.getLogger("test-main"))

    assert recovered == {"https://example.com/a": articles[0]}
    payload = json.loads(partial_path.read_text(encoding="utf-8"))
    assert payload["date"] == "2026-03-14"


def test_load_partial_results_ignores_bad_payload(tmp_path):
    partial_path = tmp_path / "2026-03-14.partial.json"
    partial_path.write_text('{"articles": "bad"}', encoding="utf-8")

    recovered = main._load_partial_results(partial_path, logging.getLogger("test-main"))

    assert recovered == {}


def test_merge_with_existing_daily_report_keeps_existing_and_adds_new():
    existing_articles = [
        {
            "title": "Existing official item",
            "url": "https://example.com/existing",
            "published": "2026-03-14T08:00:00+00:00",
            "source_name": "Example",
            "source_category": "official",
            "summary_zh": "Existing summary",
            "tags": ["official"],
            "importance": 5,
        }
    ]
    new_articles = [
        {
            "title": "New community item",
            "url": "https://example.com/new",
            "published": "2026-03-14T09:00:00+00:00",
            "source_name": "Example",
            "source_category": "community",
            "summary_zh": "New summary",
            "tags": ["community"],
            "importance": 4,
        }
    ]

    merged, changed = main._merge_with_existing_daily_report(
        existing_articles,
        new_articles,
        max_output=5,
        non_arxiv_ratio=0.5,
    )

    assert changed is True
    assert [article["url"] for article in merged] == [
        "https://example.com/existing",
        "https://example.com/new",
    ]


def test_merge_with_existing_daily_report_preserves_existing_when_no_new_items():
    existing_articles = [
        {
            "title": "Existing official item",
            "url": "https://example.com/existing",
            "published": "2026-03-14T08:00:00+00:00",
            "source_name": "Example",
            "source_category": "official",
            "summary_zh": "Existing summary",
            "tags": ["official"],
            "importance": 5,
        }
    ]

    merged, changed = main._merge_with_existing_daily_report(
        existing_articles,
        [],
        max_output=5,
        non_arxiv_ratio=0.5,
    )

    assert changed is False
    assert merged == existing_articles


def _test_config(tmp_path):
    return {
        "outputs": {"output_dir": str(tmp_path / "output")},
        "pipeline": {
            "stage1_batch_size": 10,
            "stage1_concurrency": 2,
            "stage1_selection_buffer_ratio": 1.5,
            "max_articles_to_stage2": 10,
            "stage2_concurrency": 2,
            "max_articles_per_day": 10,
            "non_arxiv_ratio": 0.5,
        },
    }


@pytest.mark.anyio
async def test_run_pipeline_preserves_existing_digest_when_no_new_articles(tmp_path, monkeypatch):
    config = _test_config(tmp_path)
    logger = logging.getLogger("test-main-pipeline")
    generated_at = datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    digest_path = output_dir / "2026-03-16.json"
    digest_path.write_text(
        json.dumps(
            {
                "date": "2026-03-16",
                "generated_at": generated_at.isoformat(),
                "articles": [
                    {
                        "title": "Existing article",
                        "url": "https://example.com/existing",
                        "published": generated_at.isoformat(),
                        "source_name": "Example",
                        "source_category": "news",
                        "summary_zh": "summary",
                        "tags": ["AI"],
                        "importance": 4,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    saved_state = {"called": False}
    generated_reports: list[list[dict]] = []

    class FakeFetcher:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger

        async def run(self):
            return []

        def save_state(self):
            saved_state["called"] = True

    monkeypatch.setattr(main, "setup_logger", lambda config: logger)
    monkeypatch.setattr(main, "now_in_config_timezone", lambda config: generated_at)
    monkeypatch.setattr(main, "FeedFetcher", FakeFetcher)
    monkeypatch.setattr(
        main,
        "generate_report",
        lambda articles, config, generated_at=None: generated_reports.append(list(articles)),
    )

    progress_updates: list[dict] = []
    result = await main.run_pipeline(config, progress_callback=progress_updates.append)

    assert result == {"result": "no_new_items", "article_count": 1}
    assert generated_reports == []
    assert saved_state["called"] is False
    assert progress_updates[-1]["report_articles"] == 1


@pytest.mark.anyio
async def test_run_pipeline_processes_and_reports_selected_articles(tmp_path, monkeypatch):
    config = _test_config(tmp_path)
    logger = logging.getLogger("test-main-pipeline-success")
    generated_at = datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc)
    saved_state = {"called": False}
    generated_reports: list[list[dict]] = []

    articles = [
        RawArticle(
            title="Alpha",
            url="https://example.com/alpha",
            published=generated_at.isoformat(),
            source_name="Example",
            source_category="news",
            summary="Alpha summary",
            content="Alpha content",
        ),
        RawArticle(
            title="Beta",
            url="https://example.com/beta",
            published=generated_at.isoformat(),
            source_name="Example",
            source_category="arxiv",
            summary="Beta summary",
            content="Beta content",
        ),
    ]

    class FakeFetcher:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger

        async def run(self):
            return articles

        def save_state(self):
            saved_state["called"] = True

    class FakeLLMClient:
        def __init__(self, config):
            self.config = config

        async def call_stage1(self, prompt):
            return [article.url for article in articles]

        async def call_stage2(self, prompt):
            if "Alpha" in prompt:
                return {"summary_zh": "Alpha zh", "tags": ["AI"], "importance": 5}
            if "Beta" in prompt:
                return {"summary_zh": "Beta zh", "tags": ["ML"], "importance": 3}
            return None

    monkeypatch.setattr(main, "setup_logger", lambda config: logger)
    monkeypatch.setattr(main, "now_in_config_timezone", lambda config: generated_at)
    monkeypatch.setattr(main, "FeedFetcher", FakeFetcher)
    monkeypatch.setattr(main, "LLMClient", FakeLLMClient)
    monkeypatch.setattr(
        main,
        "generate_report",
        lambda articles, config, generated_at=None: generated_reports.append(list(articles)) or "report.md",
    )

    progress_updates: list[dict] = []
    result = await main.run_pipeline(config, progress_callback=progress_updates.append)

    assert result == {"result": "success", "article_count": 2}
    assert saved_state["called"] is True
    assert len(generated_reports) == 1
    assert [article["url"] for article in generated_reports[0]] == [
        "https://example.com/alpha",
        "https://example.com/beta",
    ]
    assert progress_updates[-1]["stage"] == "completed"
    assert progress_updates[-1]["report_articles"] == 2
    assert not (tmp_path / "output" / "2026-03-16.partial.json").exists()


@pytest.mark.anyio
async def test_run_pipeline_cancels_other_stage1_batches_when_one_fails(tmp_path, monkeypatch):
    config = _test_config(tmp_path)
    config["pipeline"]["stage1_batch_size"] = 1
    config["pipeline"]["stage1_concurrency"] = 2
    logger = logging.getLogger("test-main-stage1-cancel")
    generated_at = datetime(2026, 3, 16, 8, 0, tzinfo=timezone.utc)

    articles = [
        RawArticle(
            title="Alpha",
            url="https://example.com/alpha",
            published=generated_at.isoformat(),
            source_name="Example",
            source_category="news",
            summary="Alpha summary",
            content="Alpha content",
        ),
        RawArticle(
            title="Beta",
            url="https://example.com/beta",
            published=generated_at.isoformat(),
            source_name="Example",
            source_category="news",
            summary="Beta summary",
            content="Beta content",
        ),
    ]
    stage1_cancelled = {"value": False}
    call_count = {"value": 0}

    class FakeFetcher:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger

        async def run(self):
            return articles

        def save_state(self):
            return None

    class FakeLLMClient:
        def __init__(self, config):
            self.config = config

        async def call_stage1(self, prompt):
            call_count["value"] += 1
            if call_count["value"] == 1:
                raise RuntimeError("stage1 failed")
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                stage1_cancelled["value"] = True
                raise
            return []

        async def call_stage2(self, prompt):
            raise AssertionError("Stage 2 should not run after Stage 1 failure")

    monkeypatch.setattr(main, "setup_logger", lambda config: logger)
    monkeypatch.setattr(main, "now_in_config_timezone", lambda config: generated_at)
    monkeypatch.setattr(main, "FeedFetcher", FakeFetcher)
    monkeypatch.setattr(main, "LLMClient", FakeLLMClient)

    with pytest.raises(RuntimeError, match="stage1 failed"):
        await main.run_pipeline(config)

    assert stage1_cancelled["value"] is True


def test_stage1_target_for_batch_uses_proportional_buffer():
    target = main._stage1_target_for_batch(
        batch_size=20,
        total_candidates=100,
        max_to_stage2=50,
        selection_buffer_ratio=1.6,
    )
    assert target == 16


def test_stage1_target_for_batch_respects_batch_size_and_minimum():
    assert (
        main._stage1_target_for_batch(
            batch_size=5,
            total_candidates=20,
            max_to_stage2=50,
            selection_buffer_ratio=2.0,
        )
        == 5
    )
    assert (
        main._stage1_target_for_batch(
            batch_size=0,
            total_candidates=20,
            max_to_stage2=50,
            selection_buffer_ratio=2.0,
        )
        == 0
    )
