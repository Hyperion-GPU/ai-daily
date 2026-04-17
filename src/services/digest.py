from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone

from dateutil import parser as date_parser

from src.server.loader import list_dates, load_digest, load_index

LoadDigestFn = Callable[[str, dict | None], dict | None]
LoadIndexFn = Callable[[dict | None], list[dict] | None]
ListDatesFn = Callable[[dict | None], list[str]]


def published_sort_key(article: dict) -> datetime:
    published = article.get("published")
    if not published:
        return datetime.min.replace(tzinfo=timezone.utc)

    try:
        parsed = date_parser.parse(str(published))
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class DigestArchiveService:
    def __init__(
        self,
        *,
        list_dates_fn: ListDatesFn = list_dates,
        load_index_fn: LoadIndexFn = load_index,
        load_digest_fn: LoadDigestFn = load_digest,
    ) -> None:
        self._list_dates_fn = list_dates_fn
        self._load_index_fn = load_index_fn
        self._load_digest_fn = load_digest_fn

    def get_dates(self, config: dict) -> dict:
        date_strings = self._list_dates_fn(config)
        index_entries = self._load_index_fn(config) or []
        stats_by_date = {
            entry.get("date"): entry
            for entry in index_entries
            if isinstance(entry.get("date"), str)
        }
        dates = []
        for date in date_strings:
            index_entry = stats_by_date.get(date)
            if index_entry:
                total = index_entry.get("total", 0)
                by_category = index_entry.get("by_category", {})
            else:
                digest = self._load_digest_fn(date, config)
                stats = digest.get("stats", {}) if digest else {}
                total = stats.get("total", 0)
                by_category = stats.get("by_category", {})
            dates.append(
                {
                    "date": date,
                    "total": total,
                    "by_category": by_category,
                }
            )
        return {"dates": dates, "latest": date_strings[0] if date_strings else None}

    def get_digest(
        self,
        config: dict,
        date: str,
        *,
        tags: list[str],
        category: str | None,
        min_importance: int,
        sort: str,
        q: str | None,
    ) -> dict | None:
        data = self._load_digest_fn(date, config)
        if data is None:
            return None

        articles = data["articles"]

        if tags:
            articles = [article for article in articles if any(tag in article["tags"] for tag in tags)]
        if category:
            articles = [article for article in articles if article["source_category"] == category]
        if min_importance > 1:
            articles = [article for article in articles if article["importance"] >= min_importance]
        if q:
            q_normalized = q.casefold()
            articles = [
                article
                for article in articles
                if q_normalized in str(article.get("title", "")).casefold()
                or q_normalized in str(article.get("summary_zh", "")).casefold()
            ]

        if sort == "published":
            articles = sorted(articles, key=published_sort_key, reverse=True)
        else:
            articles = sorted(articles, key=lambda article: article.get("importance", 0), reverse=True)

        by_category = Counter(article["source_category"] for article in articles)
        by_tag = Counter(tag for article in articles for tag in article["tags"])

        return {
            "date": data["date"],
            "generated_at": data["generated_at"],
            "stats": {
                "total": len(articles),
                "by_category": dict(by_category),
                "by_tag": dict(by_tag),
            },
            "articles": articles,
        }
