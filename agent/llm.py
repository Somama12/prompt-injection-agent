"""Thin wrapper around the Gemini API.

Adds the three things the evaluation harness needs that the raw SDK does not
give us: a process-wide rate limiter (Gemini free tier is a few requests per
minute), retry with exponential backoff on 429/503, and a call counter so the
report can state how many real API calls were made.
"""
from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", "gemini-2.0-flash")

# Requests per minute to allow across all threads. Override with GEMINI_RPM.
RPM = int(os.environ.get("GEMINI_RPM", "120"))


class LLMError(RuntimeError):
    pass


@dataclass
class _Stats:
    calls: int = 0
    retries: int = 0
    failures: int = 0
    total_latency_s: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, latency: float) -> None:
        with self.lock:
            self.calls += 1
            self.total_latency_s += latency

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "calls": self.calls,
                "retries": self.retries,
                "failures": self.failures,
                "total_latency_s": round(self.total_latency_s, 2),
                "mean_latency_s": round(self.total_latency_s / self.calls, 3) if self.calls else 0.0,
            }


STATS = _Stats()


class _RateLimiter:
    """Simple spacing limiter: guarantees >= (60 / rpm) seconds between starts."""

    def __init__(self, rpm: int) -> None:
        self._min_interval = 60.0 / max(rpm, 1)
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._next_allowed - now)
            self._next_allowed = max(now, self._next_allowed) + self._min_interval
        if wait > 0:
            time.sleep(wait)


_LIMITER = _RateLimiter(RPM)
_client = None
_client_lock = threading.Lock()


def get_client():
    """Lazily build the shared genai client so importing this module is cheap."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    raise LLMError(
                        "GEMINI_API_KEY is not set. Copy .env.example to .env and paste your key."
                    )
                from google import genai

                _client = genai.Client(api_key=api_key)
    return _client


def _is_retryable(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(
        marker in text
        for marker in (
            "429", "resource_exhausted", "rate limit", "quota",
            "503", "unavailable", "500", "internal", "deadline", "timeout",
        )
    )


def generate(
    prompt: str,
    *,
    system_instruction: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_output_tokens: int = 1024,
    max_attempts: int = 6,
) -> str:
    """Single-turn text generation. Returns the model's text, or raises LLMError."""
    from google.genai import types

    client = get_client()
    model = model or DEFAULT_MODEL
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_instruction=system_instruction,
        # Injection payloads routinely trip the default safety filters, which would
        # silently turn an *unsuccessful* attack into an API error. Disable them so
        # that what we measure is the agent's behaviour, not Google's moderation.
        safety_settings=[
            types.SafetySetting(category=c, threshold="BLOCK_NONE")
            for c in (
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
            )
        ],
    )

    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        _LIMITER.acquire()
        start = time.monotonic()
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            STATS.record(time.monotonic() - start)
            text = (resp.text or "").strip()
            if not text:
                # Empty completion (e.g. recitation / MAX_TOKENS with no text).
                # Treat as a non-answer rather than crashing the run.
                return ""
            return text
        except Exception as exc:  # noqa: BLE001 - SDK raises many concrete types
            last_exc = exc
            if not _is_retryable(exc) or attempt == max_attempts - 1:
                break
            with STATS.lock:
                STATS.retries += 1
            time.sleep(min(2**attempt + random.uniform(0, 1.0), 30.0))

    with STATS.lock:
        STATS.failures += 1
    raise LLMError(f"Gemini call failed after {max_attempts} attempts: {last_exc}")
