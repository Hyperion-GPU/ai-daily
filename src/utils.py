import logging
import os
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .runtime import get_runtime_paths

logger = logging.getLogger("aidaily")
T = TypeVar("T")


def get_config_timezone(config: dict):
    timezone_name = config.get("timezone", "Asia/Shanghai")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning(f"Timezone '{timezone_name}' not found. Falling back to UTC.")
        return ZoneInfo("UTC")


def now_in_config_timezone(config: dict) -> datetime:
    return datetime.now(get_config_timezone(config))


def setup_logger(config: dict) -> logging.Logger:
    """Initialize the application logger for stdout and daily log files."""
    app_logger = logging.getLogger("aidaily")
    app_logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    has_console_handler = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in app_logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

    out_dir = get_runtime_paths(config=config).output_dir
    os.makedirs(out_dir, exist_ok=True)

    log_filename_template = config.get("outputs", {}).get("log_filename", "{date}.log")
    date_str = now_in_config_timezone(config).strftime("%Y-%m-%d")
    log_filepath = out_dir / log_filename_template.replace("{date}", date_str)

    existing_file_handlers = [
        handler for handler in app_logger.handlers if isinstance(handler, logging.FileHandler)
    ]
    if not any(getattr(handler, "baseFilename", "") == str(log_filepath) for handler in existing_file_handlers):
        for handler in existing_file_handlers:
            app_logger.removeHandler(handler)
            handler.close()
        file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)

    return app_logger


def clean_html_tags(text: str) -> str:
    """Strip simple HTML markup and common entities from feed text."""
    if not text:
        return ""

    clean_text = re.sub(r"<[^>]+>", " ", text)
    clean_text = (
        clean_text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Trim long text to a predictable maximum length."""
    if text and len(text) > max_chars:
        return text[:max_chars] + "..."
    return text or ""


def split_by_ratio(
    items: list[T],
    ratio: float,
    max_count: int,
    is_primary: Callable[[T], bool],
    sort_key: Callable[[T], Any] | None = None,
    reverse: bool = False,
) -> list[T]:
    """Keep a ratio of primary items while preserving current selection semantics."""
    if max_count <= 0 or not items:
        return []

    ratio = max(0.0, min(1.0, ratio))
    primary = [item for item in items if is_primary(item)]
    secondary = [item for item in items if not is_primary(item)]

    if sort_key is not None:
        primary = sorted(primary, key=sort_key, reverse=reverse)
        secondary = sorted(secondary, key=sort_key, reverse=reverse)

    primary_slots = min(len(primary), int(max_count * ratio))
    secondary_slots = max_count - primary_slots
    return primary[:primary_slots] + secondary[:secondary_slots]
