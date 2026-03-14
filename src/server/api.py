from collections import Counter
from datetime import datetime, timezone

from dateutil import parser as date_parser
from fastapi import APIRouter, HTTPException, Query

from .loader import list_dates, load_digest
from .schemas import DateListResponse, DigestResponse

router = APIRouter(prefix="/api")


def _published_sort_key(article: dict) -> datetime:
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


@router.get("/dates", response_model=DateListResponse)
def get_dates():
    date_strings = list_dates()
    dates = []
    for date in date_strings:
        digest = load_digest(date)
        stats = digest.get("stats", {}) if digest else {}
        dates.append(
            {
                "date": date,
                "total": stats.get("total", 0),
                "by_category": stats.get("by_category", {}),
            }
        )
    return {"dates": dates, "latest": date_strings[0] if date_strings else None}


@router.get("/digest/{date}", response_model=DigestResponse)
def get_digest(
    date: str,
    tags: list[str] = Query(default=[]),
    category: str | None = None,
    min_importance: int = Query(default=1, ge=1, le=5),
    sort: str = Query(default="importance", pattern="^(importance|published)$"),
    q: str | None = None,
):
    data = load_digest(date)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Digest for {date} not found")

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
        articles = sorted(articles, key=_published_sort_key, reverse=True)
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
