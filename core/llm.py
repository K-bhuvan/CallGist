"""OpenAI client helpers with retries (thread-safe for parallel workers)."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

load_dotenv()

logger = logging.getLogger(__name__)

_client: OpenAI | None = None
_client_lock = threading.Lock()


def get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env")
            _client = OpenAI(api_key=api_key)
        return _client


def chat_json(
    messages: list[dict[str, str]],
    model: str,
    *,
    temperature: float = 0.2,
    max_retries: int = 3,
    retry_base_delay: float = 1.0,
) -> dict[str, Any]:
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
            return json.loads(content)
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
