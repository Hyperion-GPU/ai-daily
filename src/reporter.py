import hashlib
import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

logger = logging.getLogger("aidaily")


def _article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:6]


def generate_report(articles: list[dict], config: dict) -> Path:
    """生成 MD + JSON 双输出，返回 MD 文件路径"""
    out_dir = Path(config.get("outputs", {}).get("output_dir", "output"))
    out_dir.mkdir(exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    md_path = out_dir / config.get("outputs", {}).get("report_filename", "{date}.md").replace("{date}", date_str)
    json_path = out_dir / f"{date_str}.json"

    # 按 importance 降序排列
    articles_sorted = sorted(articles, key=lambda a: a.get("importance", 0), reverse=True)

    # 给每篇文章添加 id
    for a in articles_sorted:
        a["id"] = _article_id(a["url"])

    # === 生成 JSON ===
    by_category = dict(Counter(a["source_category"] for a in articles_sorted))
    by_tag = dict(Counter(t for a in articles_sorted for t in a.get("tags", [])))

    json_data = {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total": len(articles_sorted),
            "by_category": by_category,
            "by_tag": by_tag,
        },
        "articles": articles_sorted,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON report saved to {json_path}")

    # === 生成 Markdown ===
    lines = [f"# AI Daily — {date_str}", ""]

    highlight = [a for a in articles_sorted if a.get("importance", 0) >= 4]
    normal = [a for a in articles_sorted if a.get("importance", 0) < 4]

    if highlight:
        lines.append("## ⭐ 重点关注")
        lines.append("")
        for a in highlight:
            _append_article_md(lines, a)

    if normal:
        lines.append("## 📰 其他值得关注")
        lines.append("")
        for a in normal:
            _append_article_md(lines, a)

    if not articles_sorted:
        lines.append("_今日无符合条件的 AI 资讯。_")
        lines.append("")

    lines.append("---")
    lines.append(f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Markdown report saved to {md_path}")

    return md_path


def _append_article_md(lines: list[str], article: dict):
    title = article.get("title", "Untitled")
    url = article.get("url", "")
    source = article.get("source_name", "Unknown")
    tags_str = " · ".join(f"`{t}`" for t in article.get("tags", []))
    importance = article.get("importance", 0)
    summary = article.get("summary_zh", "")

    lines.append(f"### [{title}]({url})")
    lines.append(f"> 来源：{source} · 标签：{tags_str} · 重要性：{importance}/5")
    lines.append(f"> {summary}")
    lines.append("")
