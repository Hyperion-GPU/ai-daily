import asyncio
from unittest.mock import AsyncMock

from src.llm import LLMClient


def make_client():
    return LLMClient.__new__(LLMClient)


def test_strip_code_fence_handles_common_shapes():
    assert LLMClient._strip_code_fence("```json\n[1]\n```") == "[1]"
    assert LLMClient._strip_code_fence("plain") == "plain"
    assert LLMClient._strip_code_fence("```\nline\n```") == "line"
    assert LLMClient._strip_code_fence("") == ""


def test_call_stage1_parses_valid_json_and_deduplicates():
    client = make_client()
    client._call = AsyncMock(return_value='["https://a", "https://a", " ", 1, "https://b"]')

    result = asyncio.run(client.call_stage1("prompt"))

    assert result == ["https://a", "https://b"]


def test_call_stage1_returns_empty_on_invalid_shapes():
    client = make_client()
    client._call = AsyncMock(return_value='{"url": "https://a"}')
    assert asyncio.run(client.call_stage1("prompt")) == []

    client._call = AsyncMock(return_value="not json")
    assert asyncio.run(client.call_stage1("prompt")) == []


def test_call_stage2_parses_and_normalizes_fields():
    client = make_client()
    client._call = AsyncMock(
        return_value='{"summary_zh":"summary","tags":["AI","AI",""],"importance":"7"}'
    )

    result = asyncio.run(client.call_stage2("prompt"))

    assert result == {"summary_zh": "summary", "tags": ["AI"], "importance": 5}


def test_call_stage2_returns_none_on_invalid_payload():
    client = make_client()
    client._call = AsyncMock(return_value='{"summary_zh":"summary"}')
    assert asyncio.run(client.call_stage2("prompt")) is None

    client._call = AsyncMock(return_value="not json")
    assert asyncio.run(client.call_stage2("prompt")) is None
