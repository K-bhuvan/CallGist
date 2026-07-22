"""LLM client helpers with retries (thread-safe for parallel workers).
Supports OpenAI and any OpenAI-compatible API (OpenRouter, Together, etc.).
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from core.logging import get_logger

load_dotenv()

logger = get_logger(__name__)

_client: OpenAI | None = None
_client_lock = threading.Lock()

PRICING_PER_1K = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},
}


def _resolve_llm_config() -> tuple[str, str | None, dict[str, str]]:
    provider = os.getenv("LLM_PROVIDER", "").lower()
    base_url = os.getenv("LLM_BASE_URL", "") or None
    extra_headers: dict[str, str] = {}

    if provider == "openrouter" or "openrouter" in (base_url or ""):
        api_key = os.getenv("OPENROUTER_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        base_url = base_url or "https://openrouter.ai/api/v1"
        extra_headers["HTTP-Referer"] = os.getenv("OPENROUTER_REFERRER", "https://callgist.app")
        extra_headers["X-Title"] = "CallGist"
    else:
        api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        provider_label = provider or "LLM"
        raise RuntimeError(
            f"No API key found for {provider_label}. "
            "Set OPENAI_API_KEY or OPENROUTER_API_KEY in .env"
        )
    return api_key, base_url, extra_headers


def get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            api_key, base_url, extra_headers = _resolve_llm_config()
            kwargs: dict[str, Any] = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            if extra_headers:
                kwargs["default_headers"] = extra_headers
            _client = OpenAI(**kwargs)
            logger.info(
                "LLM client initialized (provider=%s)",
                os.getenv("LLM_PROVIDER", "openai"),
            )
        return _client


@dataclass
class LLMResponse:
    content: dict[str, Any]
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float


def _calc_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pricing = PRICING_PER_1K.get(model, PRICING_PER_1K.get("gpt-4o-mini", {"input": 0.0, "output": 0.0}))
    return (tokens_in / 1000) * pricing["input"] + (tokens_out / 1000) * pricing["output"]


def chat_json(
    messages: list[dict[str, str]],
    model: str,
    *,
    temperature: float = 0.2,
    max_retries: int = 3,
    retry_base_delay: float = 1.0,
    track_usage: bool = True,
) -> LLMResponse | dict[str, Any]:
    client = get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)

            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0
            cost = _calc_cost(model, tokens_in, tokens_out)

            logger.debug(
                "LLM call: model=%s tokens_in=%s tokens_out=%s cost=$%.6f",
                model,
                tokens_in,
                tokens_out,
                cost,
            )

            if track_usage:
                return LLMResponse(
                    content=parsed,
                    model=model,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=cost,
                )
            return parsed
        except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
            last_error = exc
            if attempt >= max_retries - 1:
                break
            delay = retry_base_delay * (2**attempt)
            logger.warning(
                "LLM request failed (attempt %s/%s): %s — retry in %.1fs",
                attempt + 1,
                max_retries,
                exc,
                delay,
            )
            time.sleep(delay)
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt >= max_retries - 1:
                break
            delay = retry_base_delay * (2**attempt)
            logger.warning("Invalid JSON from LLM — retry in %.1fs", delay)
            time.sleep(delay)

    assert last_error is not None
    raise last_error