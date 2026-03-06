import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# 加载项目根目录的 .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("aidaily")


class LLMClient:
    def __init__(self, config: dict):
        llm_cfg = config.get("llm", {})
        provider = llm_cfg.get("provider", "siliconflow")
        provider_cfg = llm_cfg.get(provider, {})

        api_key_env = provider_cfg.get("api_key_env", "SILICONFLOW_API_KEY")
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable '{api_key_env}' is not set.")

        self.client = AsyncOpenAI(
            base_url=provider_cfg.get("base_url"),
            api_key=api_key,
        )
        self.model = provider_cfg.get("model", "deepseek-ai/DeepSeek-V3")
        self.temperature = provider_cfg.get("temperature", 0.3)
        self.max_tokens = provider_cfg.get("max_tokens", 1500)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: logging.getLogger("aidaily").warning(
            f"LLM call failed, retrying (attempt {retry_state.attempt_number})..."
        ),
    )
    async def _call(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    async def call_stage1(self, prompt: str) -> list[str]:
        """Stage 1: 批量筛选，返回 URL 列表"""
        raw = await self._call(prompt)
        # 容错：去掉可能的 markdown 代码块标记
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        try:
            result = json.loads(raw)
            if isinstance(result, list):
                return [url for url in result if isinstance(url, str)]
        except json.JSONDecodeError:
            logger.error(f"Stage 1 JSON parse failed. Raw output:\n{raw[:500]}")
        return []

    async def call_stage2(self, prompt: str) -> dict | None:
        """Stage 2: 精读摘要，返回结构化 JSON dict"""
        raw = await self._call(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                # 校验必要字段
                if "summary_zh" in result and "tags" in result and "importance" in result:
                    return result
                logger.warning(f"Stage 2 response missing required fields: {list(result.keys())}")
        except json.JSONDecodeError:
            logger.error(f"Stage 2 JSON parse failed. Raw output:\n{raw[:500]}")
        return None
