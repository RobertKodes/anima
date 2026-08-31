"""OpenAI-compatible HTTP brain (llama.cpp server, LM Studio, cloud, Ollama /v1)."""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import httpx

from anima.cognition.providers.base import Completion, StreamChunk
from anima.cognition.providers.stream_http import iter_sse_token_deltas


class OpenAICompatibleBrain:
    def __init__(
        self,
        brain_id: str,
        endpoint: str,
        model: str,
        timeout: float = 60.0,
        extra: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.id = brain_id
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.extra = extra or {}
        self.headers = headers or {}

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 400) -> Completion:
        url = self.endpoint + "/chat/completions"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        started = time.perf_counter()
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.4,
            }
            payload.update(self.extra)
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
            text = _message_text(data["choices"][0].get("message") or {})
            ms = int((time.perf_counter() - started) * 1000)
            if not text.strip():
                return Completion(
                    text="",
                    brain_id=self.id,
                    latency_ms=ms,
                    ok=False,
                    error="empty model content",
                )
            return Completion(text=text.strip(), brain_id=self.id, latency_ms=ms, ok=True)
        except Exception as exc:
            ms = int((time.perf_counter() - started) * 1000)
            return Completion(text="", brain_id=self.id, latency_ms=ms, ok=False, error=str(exc))

    def stream_complete(
        self, prompt: str, *, system: str = "", max_tokens: int = 400
    ) -> Iterator[StreamChunk]:
        url = self.endpoint + "/chat/completions"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.4,
            "stream": True,
        }
        payload.update(self.extra)
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    yield from iter_sse_token_deltas(response)
        except Exception:
            result = self.complete(prompt, system=system, max_tokens=max_tokens)
            if result.text:
                yield StreamChunk("token", result.text)

    def health(self) -> dict:
        try:
            with httpx.Client(timeout=2.0, headers=self.headers) as client:
                response = client.get(self.endpoint + "/models")
            return {
                "id": self.id,
                "ok": response.status_code < 500,
                "endpoint": self.endpoint,
                "model": self.model,
                "auth": bool(self.headers.get("Authorization")),
            }
        except Exception as exc:
            return {"id": self.id, "ok": False, "endpoint": self.endpoint, "error": str(exc)}


def _message_text(message: dict) -> str:
    """Visible reply only. Do not treat chain-of-thought fields as the answer."""
    return _flatten(message.get("content")).strip()


def _flatten(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return str(value)
