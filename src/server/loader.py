import json
import re
from functools import lru_cache
from pathlib import Path

from src.runtime import get_runtime_paths

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GITHUB_TRENDING_RE = re.compile(r"^trending-(\d{4}-\d{2}-\d{2})$")
OUTPUT_DIR: Path | None = None
INDEX_PATH: Path | None = None
GITHUB_OUTPUT_DIR: Path | None = None


def _resolve_output_dir(config: dict | None = None) -> Path:
    if config is not None:
        return get_runtime_paths(config=config).output_dir
    return OUTPUT_DIR or get_runtime_paths().output_dir


def _resolve_index_path(config: dict | None = None) -> Path:
    if config is not None:
        return _resolve_output_dir(config) / "index.json"
    return INDEX_PATH or (_resolve_output_dir() / "index.json")


def _resolve_github_output_dir(config: dict | None = None) -> Path:
    if config is not None:
        return _resolve_output_dir(config) / "github"
    return GITHUB_OUTPUT_DIR or (_resolve_output_dir() / "github")


def list_dates(config: dict | None = None) -> list[str]:
    """返回所有可用日期，降序排列"""
    output_dir = _resolve_output_dir(config)
    if not output_dir.exists():
        return []
    files = output_dir.glob("*.json")
    dates = [f.stem for f in files if DATE_RE.match(f.stem)]
    return sorted(dates, reverse=True)


@lru_cache(maxsize=60)
def _load_json(path_str: str, mtime: float) -> dict | None:
    """带缓存的 JSON 加载，mtime 用于缓存失效"""
    with open(path_str, encoding="utf-8") as f:
        return json.load(f)


def load_digest(date: str, config: dict | None = None) -> dict | None:
    """加载指定日期的 JSON，文件不存在返回 None"""
    path = _resolve_output_dir(config) / f"{date}.json"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    return _load_json(str(path), mtime)


def list_github_dates(config: dict | None = None) -> list[str]:
    """返回所有 GitHub Trending 快照日期，降序排列"""
    github_output_dir = _resolve_github_output_dir(config)
    if not github_output_dir.exists():
        return []
    files = github_output_dir.glob("trending-*.json")
    dates: list[str] = []
    for file in files:
        match = GITHUB_TRENDING_RE.match(file.stem)
        if match:
            dates.append(match.group(1))
    return sorted(dates, reverse=True)


@lru_cache(maxsize=60)
def _load_github_json(path_str: str, mtime: float) -> dict | None:
    """带缓存的 GitHub Trending JSON 加载，mtime 用于缓存失效"""
    with open(path_str, encoding="utf-8") as f:
        return json.load(f)


def load_github_trending(date: str, config: dict | None = None) -> dict | None:
    """加载指定日期的 GitHub Trending 快照，文件不存在返回 None"""
    path = _resolve_github_output_dir(config) / f"trending-{date}.json"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    try:
        return _load_github_json(str(path), mtime)
    except (OSError, json.JSONDecodeError):
        return None


@lru_cache(maxsize=1)
def _load_index(path_str: str, mtime: float) -> list[dict] | None:
    with open(path_str, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        return None
    return [entry for entry in payload if isinstance(entry, dict)]


def load_index(config: dict | None = None) -> list[dict] | None:
    index_path = _resolve_index_path(config)
    if not index_path.exists():
        return None

    mtime = index_path.stat().st_mtime
    try:
        return _load_index(str(index_path), mtime)
    except (OSError, json.JSONDecodeError):
        return None
