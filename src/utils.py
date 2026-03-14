import logging
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger("aidaily")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    if app_logger.hasHandlers():
        return app_logger
    app_logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    out_dir = PROJECT_ROOT / config.get("outputs", {}).get("output_dir", "output")
    os.makedirs(out_dir, exist_ok=True)

    log_filename_template = config.get("outputs", {}).get("log_filename", "{date}.log")
    date_str = now_in_config_timezone(config).strftime("%Y-%m-%d")
    log_filepath = out_dir / log_filename_template.replace("{date}", date_str)

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
