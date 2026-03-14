import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import httpx
from dateutil import parser as date_parser

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None

from src.utils import clean_html_tags, truncate_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RawArticle:
    title: str
    url: str
    published: str
    source_name: str
    source_category: str
    summary: str
    content: str
    processed: bool = False


class FeedFetcher:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.state_file = PROJECT_ROOT / "data" / "state.json"
        self.state_file.parent.mkdir(exist_ok=True)

        pipeline_cfg = config.get("pipeline", {})
        self.time_window = pipeline_cfg.get("time_window_hours", 48)
        self.seen_url_retention_days = pipeline_cfg.get("seen_url_retention_days", 7)
        self.fetch_full_text_enabled = pipeline_cfg.get("fetch_full_text", True)
        self.full_text_max_chars = pipeline_cfg.get("full_text_max_chars", 2000)
        self.full_text_concurrency = pipeline_cfg.get("full_text_concurrency", 5)
        self.seen_urls: dict[str, str] = {}
        self._full_text_warning_logged = False
        self.load_state()

    def _seen_urls_cutoff(self) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=self.seen_url_retention_days)

    def _prune_seen_urls(self, seen_urls: dict[str, str]) -> dict[str, str]:
        cutoff = self._seen_urls_cutoff()
        pruned: dict[str, str] = {}

        for url, timestamp in seen_urls.items():
            if not isinstance(url, str) or not isinstance(timestamp, str):
                continue

            try:
                seen_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue

            if seen_at.tzinfo is None:
                seen_at = seen_at.replace(tzinfo=timezone.utc)
            else:
                seen_at = seen_at.astimezone(timezone.utc)

            if seen_at > cutoff:
                pruned[url] = seen_at.isoformat()

        return pruned

    def load_state(self):
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception as exc:
            self.logger.warning(f"Failed to load state.json: {exc}")
            return

        raw_seen_urls = data.get("seen_urls", {})
        if isinstance(raw_seen_urls, dict):
            self.seen_urls = self._prune_seen_urls(raw_seen_urls)
            return

        if isinstance(raw_seen_urls, list):
            migrated_at = datetime.now(timezone.utc).isoformat()
            self.seen_urls = {
                url: migrated_at for url in raw_seen_urls if isinstance(url, str) and url
            }
            self.logger.info("Migrated legacy seen_urls list to timestamp map.")
            return

        self.logger.warning("Unexpected seen_urls format in state.json, ignoring stored state.")
        self.seen_urls = {}

    def save_state(self):
        try:
            self.seen_urls = self._prune_seen_urls(self.seen_urls)
            with open(self.state_file, "w", encoding="utf-8") as file:
                json.dump({"seen_urls": self.seen_urls}, file, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved {len(self.seen_urls)} URLs to state.json.")
        except Exception as exc:
            self.logger.error(f"Failed to save state.json: {exc}")

    def is_within_time_window(self, date_str: str) -> bool:
        if not date_str:
            return True

        try:
            published_at = date_parser.parse(date_str)
        except Exception as exc:
            self.logger.warning(f"Failed to parse article date '{date_str}': {exc}")
            return False

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = published_at.astimezone(timezone.utc)

        diff_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        return diff_hours <= self.time_window

    def apply_arxiv_prefilter(self, feed_cfg: dict, title: str, summary: str) -> bool:
        if not feed_cfg.get("pre_filter", False):
            return True

        keywords = feed_cfg.get("keywords", "")
        if not keywords:
            return True

        pattern = re.compile(keywords, re.IGNORECASE)
        combined_text = f"{title} {summary}"
        return bool(pattern.search(combined_text))

    async def fetch_full_text(self, client: httpx.AsyncClient, url: str) -> str | None:
        if not self.fetch_full_text_enabled or not url:
            return None

        if trafilatura is None:
            if not self._full_text_warning_logged:
                self.logger.warning(
                    "trafilatura is not installed; falling back to RSS snippets for full text."
                )
                self._full_text_warning_logged = True
            return None

        try:
            response = await client.get(url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()
            extracted = trafilatura.extract(
                response.text,
                url=url,
                include_comments=False,
                include_tables=False,
                favor_recall=True,
            )
        except Exception as exc:
            self.logger.debug(f"Full text extraction failed for {url}: {exc}")
            return None

        if extracted:
            return clean_html_tags(extracted)
        return None

    async def _enrich_articles_with_full_text(
        self,
        client: httpx.AsyncClient,
        articles: list[RawArticle],
    ) -> None:
        if not articles or not self.fetch_full_text_enabled:
            return

        semaphore = asyncio.Semaphore(self.full_text_concurrency)

        async def enrich(article: RawArticle):
            async with semaphore:
                full_text = await self.fetch_full_text(client, article.url)
                if full_text:
                    article.content = truncate_text(full_text, self.full_text_max_chars)

        await asyncio.gather(*(enrich(article) for article in articles))

    async def fetch_feed(
        self,
        client: httpx.AsyncClient,
        feed_cfg: dict,
    ) -> tuple[list[RawArticle], set[str]]:
        url = feed_cfg.get("url")
        name = feed_cfg.get("name")
        category = feed_cfg.get("category")

        self.logger.info(f"Fetching RSS: {name} ...")
        articles: list[RawArticle] = []
        new_urls: set[str] = set()

        try:
            response = await client.get(url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            parsed_feed = feedparser.parse(response.text)
        except Exception as exc:
            self.logger.error(f"Failed to fetch {name}: {exc}")
            return articles, new_urls

        for entry in parsed_feed.entries:
            link = entry.get("link", "")
            if not link or link in self.seen_urls:
                continue

            title = entry.get("title", "No Title")
            published = entry.get("published", "")
            summary_raw = entry.get("summary", "")
            content_raw = summary_raw
            if "content" in entry and len(entry.content) > 0:
                content_raw = entry.content[0].get("value", summary_raw)

            summary_clean = clean_html_tags(summary_raw)
            content_clean = clean_html_tags(content_raw)

            if not self.is_within_time_window(published):
                continue

            if not self.apply_arxiv_prefilter(feed_cfg, title, summary_clean):
                continue

            new_urls.add(link)
            articles.append(
                RawArticle(
                    title=title,
                    url=link,
                    published=published,
                    source_name=name,
                    source_category=category,
                    summary=truncate_text(summary_clean, 300),
                    content=truncate_text(content_clean, self.full_text_max_chars),
                )
            )

        if category in {"news", "official", "community"}:
            await self._enrich_articles_with_full_text(client, articles)

        self.logger.info(f"Extracted {len(articles)} fresh items from {name}.")
        return articles, new_urls

    async def run(self) -> list[RawArticle]:
        feeds = [feed for feed in self.config.get("feeds", []) if feed.get("enabled", True)]
        all_articles: list[RawArticle] = []
        seen_at = datetime.now(timezone.utc).isoformat()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Daily-Bot/1.0"
        }

        async with httpx.AsyncClient(headers=headers) as client:
            results = await asyncio.gather(
                *(self.fetch_feed(client, feed) for feed in feeds),
                return_exceptions=True,
            )

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Feed task failed: {result}")
                continue

            articles, new_urls = result
            all_articles.extend(articles)
            self.seen_urls.update({url: seen_at for url in new_urls})

        self.logger.info(f"Fetch complete. Got {len(all_articles)} total candidates to process.")
        return all_articles
