from collections import Counter

from fastapi import APIRouter, HTTPException, Query

from .loader import list_dates, load_digest
from .schemas import DateListResponse, DigestResponse

router = APIRouter(prefix="/api")


@router.get("/dates", response_model=DateListResponse)
def get_dates():
    dates = list_dates()
    return {"dates": dates, "latest": dates[0] if dates else None}


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

    # 过滤
    if tags:
        articles = [a for a in articles if any(t in a["tags"] for t in tags)]
    if category:
        articles = [a for a in articles if a["source_category"] == category]
    if min_importance > 1:
        articles = [a for a in articles if a["importance"] >= min_importance]
    if q:
        q_lower = q.lower()
        articles = [
            a for a in articles
            if q_lower in a["title"].lower() or q_lower in a["summary_zh"]
        ]

    # 排序
    articles = sorted(articles, key=lambda a: a.get(sort, 0), reverse=True)

    # 重建过滤后的 stats
    by_cat = Counter(a["source_category"] for a in articles)
    by_tag = Counter(t for a in articles for t in a["tags"])

    return {
        "date": data["date"],
        "generated_at": data["generated_at"],
        "stats": {
            "total": len(articles),
            "by_category": dict(by_cat),
            "by_tag": dict(by_tag),
        },
        "articles": articles,
    }
