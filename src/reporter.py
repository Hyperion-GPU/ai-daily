import hashlib
from html import escape as html_escape
import json
import logging
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from src.io_utils import atomic_write_json, atomic_write_text
from src.runtime import get_runtime_paths
from src.utils import now_in_config_timezone

logger = logging.getLogger('aidaily')


def _article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:6]


def _write_index(index_path: Path, date_str: str, total: int, by_category: dict[str, int]) -> None:
    existing: list[dict] = []
    if index_path.exists():
        try:
            with open(index_path, encoding='utf-8') as f:
                payload = json.load(f)
            if isinstance(payload, list):
                existing = [entry for entry in payload if isinstance(entry, dict)]
        except (OSError, json.JSONDecodeError):
            logger.warning(f'Failed to read existing digest index at {index_path}, rebuilding it.')

    existing = [entry for entry in existing if entry.get('date') != date_str]
    existing.append(
        {
            'date': date_str,
            'total': total,
            'by_category': by_category,
        }
    )
    existing.sort(key=lambda entry: entry.get('date', ''), reverse=True)

    atomic_write_json(index_path, existing)
    logger.info(f'Digest index saved to {index_path}')


def _markdown_text(value) -> str:
    text = str(value).replace('\r', ' ').replace('\n', ' ').strip()
    text = html_escape(text, quote=False)
    return text.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('|', '\\|')


def _safe_markdown_url(value) -> str:
    url = str(value).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return ''
    return url.replace(' ', '%20').replace('(', '%28').replace(')', '%29')


def _markdown_code_text(value) -> str:
    return _markdown_text(value).replace('`', "'")


def generate_report(articles: list[dict], config: dict, generated_at=None) -> Path:
    """Generate both Markdown and JSON reports."""
    out_dir = get_runtime_paths(config=config).output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = generated_at or now_in_config_timezone(config)
    date_str = generated_at.strftime('%Y-%m-%d')
    md_path = out_dir / config.get('outputs', {}).get('report_filename', '{date}.md').replace('{date}', date_str)
    json_path = out_dir / f'{date_str}.json'
    index_path = out_dir / 'index.json'

    articles_sorted = sorted(articles, key=lambda a: a.get('importance', 0), reverse=True)
    articles_with_ids = [{**article, 'id': _article_id(article['url'])} for article in articles_sorted]

    by_category = dict(Counter(a['source_category'] for a in articles_sorted))
    by_tag = dict(Counter(t for a in articles_sorted for t in a.get('tags', [])))

    json_data = {
        'date': date_str,
        'generated_at': generated_at.isoformat(),
        'stats': {
            'total': len(articles_sorted),
            'by_category': by_category,
            'by_tag': by_tag,
        },
        'articles': articles_with_ids,
    }

    atomic_write_json(json_path, json_data)
    logger.info(f'JSON report saved to {json_path}')
    _write_index(index_path, date_str, len(articles_sorted), by_category)

    lines = [f'# AI Daily - {date_str}', '']

    highlights = [a for a in articles_sorted if a.get('importance', 0) >= 4]
    normal = [a for a in articles_sorted if a.get('importance', 0) < 4]

    if highlights:
        lines.append('## Highlights')
        lines.append('')
        for article in highlights:
            _append_article_md(lines, article)

    if normal:
        lines.append('## More Updates')
        lines.append('')
        for article in normal:
            _append_article_md(lines, article)

    if not articles_sorted:
        lines.append('_No new high-value AI updates today._')
        lines.append('')

    lines.append('---')
    lines.append(f"_Generated at {generated_at.strftime('%Y-%m-%d %H:%M %Z')}_")

    atomic_write_text(md_path, '\n'.join(lines))
    logger.info(f'Markdown report saved to {md_path}')

    return md_path


def _append_article_md(lines: list[str], article: dict):
    title = _markdown_text(article.get('title', 'Untitled'))
    url = _safe_markdown_url(article.get('url', ''))
    source = _markdown_text(article.get('source_name', 'Unknown'))
    tags = article.get('tags', [])
    tags_str = ' | '.join(f'`{_markdown_code_text(tag)}`' for tag in tags) if tags else 'N/A'
    importance = article.get('importance', 0)
    summary = _markdown_text(article.get('summary_zh', ''))

    if url:
        lines.append(f'### [{title}]({url})')
    else:
        lines.append(f'### {title}')
    lines.append(f'> Source: {source} | Tags: {tags_str} | Importance: {importance}/5')
    lines.append(f'> {summary}')
    lines.append('')
