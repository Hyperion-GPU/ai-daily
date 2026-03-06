import asyncio
import feedparser
import httpx
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from dateutil import parser as date_parser
from dataclasses import dataclass, asdict
from typing import List, Dict, Set

from src.utils import clean_html_tags, truncate_text

@dataclass
class RawArticle:
    title: str
    url: str
    published: str
    source_name: str
    source_category: str
    summary: str
    content: str
    processed: bool = False

class FeedFetcher:
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.state_file = Path("data") / "state.json"
        self.state_file.parent.mkdir(exist_ok=True)
        self.seen_urls: Set[str] = set()
        self.load_state()
        
        pipeline_cfg = config.get("pipeline", {})
        self.time_window = pipeline_cfg.get("time_window_hours", 48)

    def load_state(self):
        """加载已处理的 URL，防止重复抓取和调用大模型"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seen_urls = set(data.get("seen_urls", []))
            except Exception as e:
                self.logger.warning(f"Failed to load state.json: {e}")

    def save_state(self):
        """持久化保存已处理的 URL"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({"seen_urls": list(self.seen_urls)}, f, ensure_ascii=False, indent=2)
            self.logger.info(f"💾 Saved {len(self.seen_urls)} URLs to state.json.")
        except Exception as e:
            self.logger.error(f"Failed to save state.json: {e}")

    def is_within_time_window(self, date_str: str) -> bool:
        """检查文章发布时间是否在有效窗口内（防挖坟）"""
        if not date_str:
            return True # 容错
            
        try:
            pub_date = date_parser.parse(date_str)
            # 统一转为 UTC 时间进行比较
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            else:
                pub_date = pub_date.astimezone(timezone.utc)
            
            now_utc = datetime.now(timezone.utc)
            diff_hours = (now_utc - pub_date).total_seconds() / 3600
            return diff_hours <= self.time_window
            
        except Exception as e:
            self.logger.debug(f"Failed to parse article date: {date_str}, Error: {e}")
            return True # parse 失败放行

    def apply_arxiv_prefilter(self, feed_cfg: dict, title: str, summary: str) -> bool:
        """如果配置了关键词预过滤，正则匹配通过才放行"""
        if not feed_cfg.get("pre_filter", False):
            return True
            
        keywords = feed_cfg.get("keywords", "")
        if not keywords:
            return True
            
        pattern = re.compile(keywords, re.IGNORECASE)
        combined_text = f"{title} {summary}"
        return bool(pattern.search(combined_text))

    async def fetch_feed(self, client: httpx.AsyncClient, feed_cfg: dict, new_urls_batch: Set) -> List[RawArticle]:
        """抓取单个 RSS 源"""
        url = feed_cfg.get("url")
        name = feed_cfg.get("name")
        cat = feed_cfg.get("category")
        
        self.logger.info(f"📡 Fetching RSS: {name} ...")
        articles = []
        try:
            # RSS 源经常连接缓慢或被墙，设一个较大的 timeout
            response = await client.get(url, timeout=20.0, follow_redirects=True)
            response.raise_for_status()
            parsed_feed = feedparser.parse(response.text)
            
            for entry in parsed_feed.entries:
                link = entry.get('link', '')
                if not link or link in self.seen_urls:
                    continue
                    
                title = entry.get('title', 'No Title')
                pub_date = entry.get('published', '')
                
                # 提取摘要和正文，有些 Feed 只有 summary 没有 content
                summary_raw = entry.get('summary', '') 
                content_raw = summary_raw
                if 'content' in entry and len(entry.content) > 0:
                     content_raw = entry.content[0].get('value', summary_raw)
                     
                summary_clean = clean_html_tags(summary_raw)
                content_clean = clean_html_tags(content_raw)
                
                # 1. 48小时过滤
                if not self.is_within_time_window(pub_date):
                    continue
                    
                # 2. Arxiv 关键词正则预过滤
                if not self.apply_arxiv_prefilter(feed_cfg, title, summary_clean):
                    continue
                    
                new_urls_batch.add(link)
                articles.append(RawArticle(
                    title=title,
                    url=link,
                    published=pub_date,
                    source_name=name,
                    source_category=cat,
                    summary=truncate_text(summary_clean, 300),
                    content=truncate_text(content_clean, 500)
                ))
            self.logger.info(f"✅ Extracted {len(articles)} fresh items from {name}.")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch {name}: {e}")
            
        return articles

    async def run(self) -> List[RawArticle]:
        feeds = [f for f in self.config.get("feeds", []) if f.get("enabled", True)]
        all_articles = []
        new_urls_batch = set()
        
        # 常见 feed 可能会封禁无 User-Agent 的爬虫
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Daily-Bot/1.0'}
        
        async with httpx.AsyncClient(headers=headers) as client:
            tasks = [self.fetch_feed(client, f, new_urls_batch) for f in feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, list):
                    all_articles.extend(res)
                    
        self.seen_urls.update(new_urls_batch)
        self.logger.info(f"🎉 Fetch complete. Got {len(all_articles)} total candidates to process.")
        return all_articles
