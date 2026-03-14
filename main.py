import argparse
import asyncio
import sys
from pathlib import Path

import yaml
from jinja2 import Template

from src.fetcher import FeedFetcher
from src.llm import LLMClient
from src.reporter import generate_report
from src.utils import setup_logger

BASE_DIR = Path(__file__).resolve().parent


async def run_pipeline(config: dict, dry_run: bool = False):
    logger = setup_logger(config)
    logger.info("=== AI Daily Pipeline Start ===")

    pipeline_cfg = config.get("pipeline", {})
    stage1_batch_size = pipeline_cfg.get("stage1_batch_size", 50)
    max_to_stage2 = pipeline_cfg.get("max_articles_to_stage2", 50)
    stage2_concurrency = pipeline_cfg.get("stage2_concurrency", 5)
    max_output = pipeline_cfg.get("max_articles_per_day", 30)
    non_arxiv_ratio = float(pipeline_cfg.get("non_arxiv_ratio", 0.4))
    non_arxiv_ratio = max(0.0, min(1.0, non_arxiv_ratio))

    fetcher = FeedFetcher(config, logger)
    all_articles = await fetcher.run()

    if not all_articles:
        logger.warning("No articles fetched. Exiting.")
        return

    logger.info(f"Fetched {len(all_articles)} candidate articles.")

    if dry_run:
        logger.info("=== DRY RUN: printing candidates, skipping LLM ===")
        for index, article in enumerate(all_articles, 1):
            logger.info(f"  [{index}] [{article.source_category}] {article.title}")
            logger.info(f"       {article.url}")
        logger.info(f"Total: {len(all_articles)} articles. Dry run complete.")
        return

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

    passed = [article for article in all_articles if article.url in selected_urls]
    non_arxiv = [article for article in passed if article.source_category != "arxiv"]
    arxiv_only = [article for article in passed if article.source_category == "arxiv"]
    non_arxiv_slots = min(len(non_arxiv), int(max_to_stage2 * non_arxiv_ratio))
    arxiv_slots = max_to_stage2 - non_arxiv_slots
    filtered = non_arxiv[:non_arxiv_slots] + arxiv_only[:arxiv_slots]
    logger.info(
        f"Stage 1 complete: {len(filtered)} articles passed "
        f"(from {len(passed)} selected, {len(all_articles)} candidates, "
        f"{non_arxiv_slots} non-arxiv + {min(len(arxiv_only), arxiv_slots)} arxiv)"
    )

    if not filtered:
        logger.warning("Stage 1 filtered out all articles. Generating empty report.")
        generate_report([], config)
        fetcher.save_state()
        return

    stage2_template = Template((BASE_DIR / "prompts" / "stage2_summary.txt").read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(stage2_concurrency)

    async def process_article(article):
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

        logger.info(f"  Stage 2 done: {article.title[:60]}...")
        return {
            "title": article.title,
            "url": article.url,
            "published": article.published,
            "source_name": article.source_name,
            "source_category": article.source_category,
            "summary_zh": summary_data.get("summary_zh", ""),
            "tags": summary_data.get("tags", []),
            "importance": summary_data.get("importance", 1),
        }

    tasks = [process_article(article) for article in filtered]
    results = [result for result in await asyncio.gather(*tasks) if result is not None]

    logger.info(f"Stage 2 complete: {len(results)}/{len(filtered)} articles processed successfully")

    non_arxiv_results = sorted(
        [article for article in results if article.get("source_category") != "arxiv"],
        key=lambda article: article.get("importance", 0),
        reverse=True,
    )
    arxiv_results = sorted(
        [article for article in results if article.get("source_category") == "arxiv"],
        key=lambda article: article.get("importance", 0),
        reverse=True,
    )
    non_arxiv_output_slots = min(len(non_arxiv_results), int(max_output * non_arxiv_ratio))
    arxiv_output_slots = max_output - non_arxiv_output_slots
    results_final = non_arxiv_results[:non_arxiv_output_slots] + arxiv_results[:arxiv_output_slots]
    results_final.sort(key=lambda article: article.get("importance", 0), reverse=True)

    md_path = generate_report(results_final, config)
    logger.info(f"Report generated: {md_path}")

    fetcher.save_state()
    logger.info(f"=== AI Daily Pipeline Complete === ({len(results_final)} articles in report)")


def main():
    parser = argparse.ArgumentParser(description="AI Daily - AI news digest generator")
    parser.add_argument("--dry-run", action="store_true", help="Only fetch RSS, skip LLM calls")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    asyncio.run(run_pipeline(config, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
