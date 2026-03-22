import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Callable, Literal, TypedDict

import yaml
from jinja2 import Template

from src.fetcher import FeedFetcher
from src.llm import LLMClient
from src.reporter import generate_report
from src.utils import now_in_config_timezone, setup_logger, split_by_ratio

BASE_DIR = Path(__file__).resolve().parent


class ProcessedArticle(TypedDict):
    title: str
    url: str
    published: str
    source_name: str
    source_category: str
    summary_zh: str
    tags: list[str]
    importance: int


class PipelineRunResult(TypedDict):
    result: Literal["success", "no_new_items", "dry_run"]
    article_count: int


class PipelineProgress(TypedDict, total=False):
    stage: Literal["starting", "fetching", "stage1", "stage2", "finalizing", "completed", "error"]
    message: str
    current: int
    total: int
    candidates: int
    selected: int
    processed: int
    report_articles: int


def _output_dir(config: dict) -> Path:
    return BASE_DIR / config.get("outputs", {}).get("output_dir", "output")


def _digest_path(config: dict, date_str: str) -> Path:
    return _output_dir(config) / f"{date_str}.json"


def _partial_path(config: dict, date_str: str) -> Path:
    return _output_dir(config) / f"{date_str}.partial.json"


def load_config(config_path: str | Path = "config.yaml") -> dict:
    resolved_path = Path(config_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _load_existing_digest_articles(config: dict, date_str: str, logger) -> list[ProcessedArticle]:
    digest_path = _digest_path(config, date_str)
    if not digest_path.exists():
        return []

    try:
        payload = json.loads(digest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning(f"Failed to read existing digest: {digest_path}")
        return []

    articles = payload.get("articles", [])
    if not isinstance(articles, list):
        logger.warning(f"Ignoring malformed digest payload: {digest_path}")
        return []

    recovered: list[ProcessedArticle] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = article.get("url")
        if not isinstance(url, str) or not url:
            continue
        recovered.append(article)
    return recovered


def _finalize_report_articles(
    articles: list[ProcessedArticle],
    max_output: int,
    non_arxiv_ratio: float,
) -> list[ProcessedArticle]:
    finalized = split_by_ratio(
        articles,
        non_arxiv_ratio,
        max_output,
        is_primary=lambda article: article["source_category"] != "arxiv",
        sort_key=lambda article: article.get("importance", 0),
        reverse=True,
    )
    finalized.sort(key=lambda article: article.get("importance", 0), reverse=True)
    return finalized


def _article_signature(articles: list[ProcessedArticle]) -> tuple[str, ...]:
    return tuple(str(article.get("url", "")) for article in articles)


def _merge_with_existing_daily_report(
    existing_articles: list[ProcessedArticle],
    new_articles: list[ProcessedArticle],
    max_output: int,
    non_arxiv_ratio: float,
) -> tuple[list[ProcessedArticle], bool]:
    existing_final = _finalize_report_articles(existing_articles, max_output, non_arxiv_ratio)
    if not existing_final:
        new_final = _finalize_report_articles(new_articles, max_output, non_arxiv_ratio)
        return new_final, bool(new_final)

    merged_by_url = {
        article["url"]: article
        for article in existing_final
        if isinstance(article.get("url"), str) and article["url"]
    }
    for article in new_articles:
        url = article.get("url")
        if isinstance(url, str) and url:
            merged_by_url[url] = article

    merged_final = _finalize_report_articles(list(merged_by_url.values()), max_output, non_arxiv_ratio)
    changed = _article_signature(merged_final) != _article_signature(existing_final)
    return (merged_final if changed else existing_final), changed


def _load_partial_results(partial_path: Path, logger) -> dict[str, ProcessedArticle]:
    if not partial_path.exists():
        return {}

    try:
        payload = json.loads(partial_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning(f"Failed to read partial checkpoint: {partial_path}")
        return {}

    if not isinstance(payload, dict):
        logger.warning(f"Ignoring malformed partial checkpoint: {partial_path}")
        return {}

    articles = payload.get("articles", [])
    if not isinstance(articles, list):
        logger.warning(f"Ignoring malformed partial checkpoint: {partial_path}")
        return {}

    recovered: dict[str, ProcessedArticle] = {}
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = article.get("url")
        if not isinstance(url, str) or not url:
            continue
        recovered[url] = article
    return recovered


def _write_partial_results(partial_path: Path, date_str: str, articles: list[ProcessedArticle]) -> None:
    partial_path.parent.mkdir(exist_ok=True)
    payload = {
        "date": date_str,
        "articles": articles,
    }
    partial_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _emit_progress(
    progress_callback: Callable[[PipelineProgress], None] | None,
    **payload: object,
) -> None:
    if progress_callback is None:
        return

    progress = payload.copy()
    progress_callback(progress)  # type: ignore[arg-type]


async def run_pipeline(
    config: dict,
    dry_run: bool = False,
    progress_callback: Callable[[PipelineProgress], None] | None = None,
) -> PipelineRunResult:
    logger = setup_logger(config)
    logger.info("=== AI Daily Pipeline Start ===")
    generated_at = now_in_config_timezone(config)
    date_str = generated_at.strftime("%Y-%m-%d")
    partial_path = _partial_path(config, date_str)
    _emit_progress(progress_callback, stage="fetching", message="Fetching feeds")

    pipeline_cfg = config.get("pipeline", {})
    stage1_batch_size = pipeline_cfg.get("stage1_batch_size", 50)
    max_to_stage2 = pipeline_cfg.get("max_articles_to_stage2", 50)
    stage2_concurrency = pipeline_cfg.get("stage2_concurrency", 5)
    max_output = pipeline_cfg.get("max_articles_per_day", 30)
    non_arxiv_ratio = float(pipeline_cfg.get("non_arxiv_ratio", 0.4))
    non_arxiv_ratio = max(0.0, min(1.0, non_arxiv_ratio))
    existing_articles = _load_existing_digest_articles(config, date_str, logger)

    fetcher = FeedFetcher(config, logger)
    all_articles = await fetcher.run()

    if not all_articles:
        logger.warning("No articles fetched. Exiting.")
        _emit_progress(
            progress_callback,
            stage="completed",
            message="No new articles found",
            candidates=0,
            selected=0,
            processed=0,
            report_articles=len(existing_articles),
        )
        if existing_articles:
            logger.info("No fresh items found. Preserving the existing daily digest.")
            return {"result": "no_new_items", "article_count": len(existing_articles)}
        generate_report([], config, generated_at=generated_at)
        return {"result": "no_new_items", "article_count": 0}

    logger.info(f"Fetched {len(all_articles)} candidate articles.")
    _emit_progress(
        progress_callback,
        stage="stage1",
        message="Filtering candidate articles",
        current=0,
        total=max(1, len(all_articles)),
        candidates=len(all_articles),
        selected=0,
        processed=0,
    )

    if dry_run:
        logger.info("=== DRY RUN: printing candidates, skipping LLM ===")
        for index, article in enumerate(all_articles, 1):
            logger.info(f"  [{index}] [{article.source_category}] {article.title}")
            logger.info(f"       {article.url}")
        logger.info(f"Total: {len(all_articles)} articles. Dry run complete.")
        _emit_progress(
            progress_callback,
            stage="completed",
            message="Dry run complete",
            candidates=len(all_articles),
            selected=len(all_articles),
            processed=0,
            report_articles=0,
        )
        return {"result": "dry_run", "article_count": len(all_articles)}

    llm = LLMClient(config)
    stage1_template = Template((BASE_DIR / "prompts" / "stage1_filter.txt").read_text(encoding="utf-8"))

    selected_urls = set()
    batches = [all_articles[i:i + stage1_batch_size] for i in range(0, len(all_articles), stage1_batch_size)]

    for batch_idx, batch in enumerate(batches, 1):
        logger.info(f"Stage 1 batch {batch_idx}/{len(batches)}: {len(batch)} articles")
        article_lines = "\n".join(
            f"- Title: {article.title} | URL: {article.url} | Source: {article.source_name}"
            for article in batch
        )
        prompt = stage1_template.render(target_count=max_to_stage2) + "\n\n" + article_lines
        urls = await llm.call_stage1(prompt)
        selected_urls.update(urls)
        logger.info(f"  Stage 1 batch {batch_idx} selected {len(urls)} URLs")
        _emit_progress(
            progress_callback,
            stage="stage1",
            message="Filtering candidate articles",
            current=batch_idx,
            total=len(batches),
            candidates=len(all_articles),
            selected=len(selected_urls),
            processed=0,
        )

    passed = [article for article in all_articles if article.url in selected_urls]
    filtered = split_by_ratio(
        passed,
        non_arxiv_ratio,
        max_to_stage2,
        is_primary=lambda article: article.source_category != "arxiv",
    )
    filtered_non_arxiv = sum(1 for article in filtered if article.source_category != "arxiv")
    filtered_arxiv = len(filtered) - filtered_non_arxiv
    logger.info(
        f"Stage 1 complete: {len(filtered)} articles passed "
        f"(from {len(passed)} selected, {len(all_articles)} candidates, "
        f"{filtered_non_arxiv} non-arxiv + {filtered_arxiv} arxiv)"
    )
    _emit_progress(
        progress_callback,
        stage="stage2",
        message="Summarizing selected articles",
        current=0,
        total=len(filtered),
        candidates=len(all_articles),
        selected=len(filtered),
        processed=0,
    )

    if not filtered:
        logger.warning("Stage 1 filtered out all articles. Generating empty report.")
        if existing_articles:
            logger.info("No new reportable items. Preserving the existing daily digest.")
        else:
            generate_report([], config, generated_at=generated_at)
        if partial_path.exists():
            partial_path.unlink()
        fetcher.save_state()
        _emit_progress(
            progress_callback,
            stage="completed",
            message="No articles passed filtering",
            candidates=len(all_articles),
            selected=0,
            processed=0,
            report_articles=len(existing_articles),
        )
        return {
            "result": "no_new_items",
            "article_count": len(existing_articles),
        }

    stage2_template = Template((BASE_DIR / "prompts" / "stage2_summary.txt").read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(stage2_concurrency)
    partial_results = _load_partial_results(partial_path, logger)
    partial_lock = asyncio.Lock()

    if partial_results:
        logger.info(f"Recovered {len(partial_results)} cached Stage 2 results from {partial_path.name}")

    async def process_article(article) -> ProcessedArticle | None:
        cached = partial_results.get(article.url)
        if cached is not None:
            logger.info(f"  Stage 2 cached: {article.title[:60]}...")
            return cached

        try:
            async with semaphore:
                prompt = stage2_template.render(
                    title=article.title,
                    content=article.content or article.summary,
                )
                summary_data = await llm.call_stage2(prompt)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"  Stage 2 failed for: {article.title[:60]}... ({exc})")
            return None

        if not summary_data:
            logger.warning(f"  Stage 2 failed for: {article.title[:60]}...")
            return None

        result: ProcessedArticle = {
            "title": article.title,
            "url": article.url,
            "published": article.published,
            "source_name": article.source_name,
            "source_category": article.source_category,
            "summary_zh": summary_data.get("summary_zh", ""),
            "tags": summary_data.get("tags", []),
            "importance": summary_data.get("importance", 1),
        }
        async with partial_lock:
            partial_results[article.url] = result
            _write_partial_results(partial_path, date_str, list(partial_results.values()))

        logger.info(f"  Stage 2 done: {article.title[:60]}...")
        return result

    tasks = [asyncio.create_task(process_article(article)) for article in filtered]
    results: list[ProcessedArticle] = []
    completed = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        completed += 1
        if result is not None:
            results.append(result)
        _emit_progress(
            progress_callback,
            stage="stage2",
            message="Summarizing selected articles",
            current=completed,
            total=len(filtered),
            candidates=len(all_articles),
            selected=len(filtered),
            processed=len(results),
        )

    logger.info(f"Stage 2 complete: {len(results)}/{len(filtered)} articles processed successfully")
    _emit_progress(
        progress_callback,
        stage="finalizing",
        message="Building today's digest",
        candidates=len(all_articles),
        selected=len(filtered),
        processed=len(results),
    )

    report_articles, report_changed = _merge_with_existing_daily_report(
        existing_articles,
        results,
        max_output,
        non_arxiv_ratio,
    )

    if not report_changed and existing_articles:
        logger.info("No new visible items for today's digest. Keeping the existing report unchanged.")
        if partial_path.exists():
            partial_path.unlink()
            logger.info(f"Cleared partial checkpoint: {partial_path.name}")
        fetcher.save_state()
        logger.info("=== AI Daily Pipeline Complete === (no new items added to today's report)")
        _emit_progress(
            progress_callback,
            stage="completed",
            message="No new items added to today's digest",
            candidates=len(all_articles),
            selected=len(filtered),
            processed=len(results),
            report_articles=len(report_articles),
        )
        return {"result": "no_new_items", "article_count": len(report_articles)}

    md_path = generate_report(report_articles, config, generated_at=generated_at)
    logger.info(f"Report generated: {md_path}")
    if partial_path.exists():
        partial_path.unlink()
        logger.info(f"Cleared partial checkpoint: {partial_path.name}")

    fetcher.save_state()
    logger.info(f"=== AI Daily Pipeline Complete === ({len(report_articles)} articles in report)")
    _emit_progress(
        progress_callback,
        stage="completed",
        message="Today's digest is ready",
        candidates=len(all_articles),
        selected=len(filtered),
        processed=len(results),
        report_articles=len(report_articles),
    )
    return {"result": "success", "article_count": len(report_articles)}


def main():
    parser = argparse.ArgumentParser(description="AI Daily - AI news digest generator")
    parser.add_argument("--dry-run", action="store_true", help="Only fetch RSS, skip LLM calls")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    asyncio.run(run_pipeline(config, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
