import logging
import os
import re
from datetime import datetime
from pathlib import Path

def setup_logger(config: dict) -> logging.Logger:
    """初始化日志，同时支持 stdout 和文件持久化写入"""
    logger = logging.getLogger("aidaily")
    if logger.hasHandlers():
        return logger
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    out_dir = config.get("outputs", {}).get("output_dir", "output")
    os.makedirs(out_dir, exist_ok=True)
    
    log_filename_template = config.get("outputs", {}).get("log_filename", "{date}.log")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    log_filepath = Path(out_dir) / log_filename_template.replace("{date}", date_str)
    
    fh = logging.FileHandler(log_filepath, encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def clean_html_tags(text: str) -> str:
    """清理文本中的 HTML 标签，返回纯文本，降低 Token 消耗"""
    if not text:
        return ""
    # 去除基本的 HTML 标签
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    # 处理常见实体字符
    clean_text = clean_text.replace("&nbsp;", " ") \
                           .replace("&amp;", "&") \
                           .replace("&lt;", "<") \
                           .replace("&gt;", ">") \
                           .replace("&#39;", "'") \
                           .replace("&quot;", '"')
    # 合并多余的空格与换行
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def truncate_text(text: str, max_chars: int = 500) -> str:
    """截断文本，如果超出 max_chars，保留前 max_chars"""
    if text and len(text) > max_chars:
        return text[:max_chars] + "..."
    return text or ""
