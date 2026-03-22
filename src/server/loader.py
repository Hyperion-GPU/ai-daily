import json
import re
from functools import lru_cache
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
INDEX_PATH = OUTPUT_DIR / "index.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GITHUB_OUTPUT_DIR = OUTPUT_DIR / "github"
GITHUB_TRENDING_RE = re.compile(r"^trending-(\d{4}-\d{2}-\d{2})$")


def list_dates() -> list[str]:
    """返回所有可用日期，降序排列"""
    if not OUTPUT_DIR.exists():
        return []
    files = OUTPUT_DIR.glob("*.json")
    dates = [f.stem for f in files if DATE_RE.match(f.stem)]
    return sorted(dates, reverse=True)


@lru_cache(maxsize=60)
def _load_json(date: str, mtime: float) -> dict | None:
    """带缓存的 JSON 加载，mtime 用于缓存失效"""
    path = OUTPUT_DIR / f"{date}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_digest(date: str) -> dict | None:
    """加载指定日期的 JSON，文件不存在返回 None"""
    path = OUTPUT_DIR / f"{date}.json"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    return _load_json(date, mtime)


def list_github_dates() -> list[str]:
    """返回所有 GitHub Trending 快照日期，降序排列"""
    if not GITHUB_OUTPUT_DIR.exists():
        return []
    files = GITHUB_OUTPUT_DIR.glob("trending-*.json")
    dates: list[str] = []
    for file in files:
        match = GITHUB_TRENDING_RE.match(file.stem)
        if match:
            dates.append(match.group(1))
    return sorted(dates, reverse=True)


@lru_cache(maxsize=60)
def _load_github_json(date: str, mtime: float) -> dict | None:
    """带缓存的 GitHub Trending JSON 加载，mtime 用于缓存失效"""
    path = GITHUB_OUTPUT_DIR / f"trending-{date}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_github_trending(date: str) -> dict | None:
    """加载指定日期的 GitHub Trending 快照，文件不存在返回 None"""
    path = GITHUB_OUTPUT_DIR / f"trending-{date}.json"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    try:
        return _load_github_json(date, mtime)
    except (OSError, json.JSONDecodeError):
        return None


@lru_cache(maxsize=1)
def _load_index(mtime: float) -> list[dict] | None:
    with open(INDEX_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        return None
    return [entry for entry in payload if isinstance(entry, dict)]


def load_index() -> list[dict] | None:
    if not INDEX_PATH.exists():
        return None

    mtime = INDEX_PATH.stat().st_mtime
    try:
        return _load_index(mtime)
    except (OSError, json.JSONDecodeError):
        return None
