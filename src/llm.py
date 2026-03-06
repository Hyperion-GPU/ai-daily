import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

logger = logging.getLogger('aidaily')


class LLMClient:
    def __init__(self, config: dict):
        llm_cfg = config.get('llm', {})
        provider = llm_cfg.get('provider', 'siliconflow')
        provider_cfg = llm_cfg.get(provider, {})

        api_key_env = provider_cfg.get('api_key_env', 'SILICONFLOW_API_KEY')
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable '{api_key_env}' is not set.")

        self.client = AsyncOpenAI(
            base_url=provider_cfg.get('base_url'),
            api_key=api_key,
        )
        self.model = provider_cfg.get('model', 'deepseek-ai/DeepSeek-V3')
        self.temperature = provider_cfg.get('temperature', 0.3)
        self.max_tokens = provider_cfg.get('max_tokens', 1500)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: logging.getLogger('aidaily').warning(
            f'LLM call failed, retrying (attempt {retry_state.attempt_number})...'
        ),
    )
    async def _call(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        text = text.strip()
        if not text.startswith('```'):
            return text
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text[:-3]
        return text.strip()

    async def call_stage1(self, prompt: str) -> list[str]:
        raw = self._strip_code_fence(await self._call(prompt))
        try:
            result = json.loads(raw)
            if not isinstance(result, list):
                return []

            seen = set()
            urls: list[str] = []
            for item in result:
                if not isinstance(item, str):
                    continue
                url = item.strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                urls.append(url)
            return urls
        except json.JSONDecodeError:
            logger.error(f'Stage 1 JSON parse failed. Raw output:\n{raw[:500]}')
            return []

    async def call_stage2(self, prompt: str) -> dict | None:
        raw = self._strip_code_fence(await self._call(prompt))
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                return None

            if 'summary_zh' not in result or 'tags' not in result or 'importance' not in result:
                logger.warning(f"Stage 2 response missing required fields: {list(result.keys())}")
                return None

            summary = str(result.get('summary_zh', '')).strip()

            tags_raw = result.get('tags', [])
            tags: list[str] = []
            if isinstance(tags_raw, list):
                for tag in tags_raw:
                    if not isinstance(tag, str):
                        continue
                    value = tag.strip()
                    if value and value not in tags:
                        tags.append(value)

            try:
                importance = int(result.get('importance', 1))
            except (TypeError, ValueError):
                importance = 1
            importance = max(1, min(5, importance))

            if not summary:
                return None

            return {
                'summary_zh': summary,
                'tags': tags,
                'importance': importance,
            }
        except json.JSONDecodeError:
            logger.error(f'Stage 2 JSON parse failed. Raw output:\n{raw[:500]}')
            return None
