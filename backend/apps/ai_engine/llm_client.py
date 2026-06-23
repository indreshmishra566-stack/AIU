"""
AIU — AI Engine: LLM Client
Uses Groq (FREE) — llama3-70b-8192 model.
Groq is free at: https://console.groq.com
Supports: llama3-70b-8192, llama3-8b-8192, mixtral-8x7b-32768, gemma2-9b-it
"""

import logging
import time

import backoff
from groq import Groq, RateLimitError, APIStatusError
from django.conf import settings

logger = logging.getLogger("ai_engine")

AI_SETTINGS = settings.AI_ENGINE


class LLMClient:
    """
    Groq LLM client — completely free tier available.
    Rate limits on free: 30 req/min, 14,400 req/day (very generous).
    """

    def __init__(self):
        self._client = None
        self.model = AI_SETTINGS["MODEL"]
        self.provider = AI_SETTINGS["PROVIDER"]

    def _get_client(self) -> Groq:
        if self._client is not None:
            return self._client

        api_key = AI_SETTINGS["GROQ_API_KEY"]
        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self._client = Groq(api_key=api_key)
        return self._client

    @backoff.on_exception(
        backoff.expo,
        (RateLimitError, APIStatusError),
        max_tries=AI_SETTINGS["MAX_RETRIES"],
        on_backoff=lambda d: logger.warning("Groq backoff", extra={"details": str(d)}),
    )
    def complete(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
    ) -> dict:
        """
        Call Groq API. Returns normalized response dict.
        Groq is OpenAI-compatible so the response format is identical.
        """
        max_tokens = max_tokens or AI_SETTINGS["MAX_TOKENS"]
        temperature = temperature if temperature is not None else AI_SETTINGS["TEMPERATURE"]
        client = self._get_client()

        start = time.perf_counter()

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
        )

        if stream:
            return response  # return iterator for streaming

        latency = (time.perf_counter() - start) * 1000
        logger.info(
            "Groq response",
            extra={
                "model": self.model,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "latency_ms": round(latency, 2),
            },
        )

        return {
            "content": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "model": self.model,
        }
