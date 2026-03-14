import json
from functools import lru_cache
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def list_dates() -> list[str]:
    """返回所有可用日期，降序排列"""
    if not OUTPUT_DIR.exists():
        return []
    files = OUTPUT_DIR.glob("*.json")
    dates = [f.stem for f in files]
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
