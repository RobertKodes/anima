"""Ollama via the native /api/chat endpoint so `think: false` actually lands in content."""

from __future__ import annotations

import time

import httpx

from anima.cognition.providers.base import Completion
from anima.cognition.providers.openai_compatible import OpenAICompatibleBrain, _message_text


class OllamaBrain(OpenAICompatibleBrain):
    def __init__(self, brain_id: str, endpoint: str = "http://127.0.0.1:11434/v1", model: str = "qwen3:1.7b") -> None:
        super().__init__(brain_id, endpoint, model, timeout=120.0)

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 400) -> Completion:
        url = self._native_root() + "/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "think": False,
                        "options": {"num_predict": max_tokens, "temperature": 0.4},
                    },
                )
                response.raise_for_status()
                data = response.json()
            text = _message_text(data.get("message") or {})
            ms = int((time.perf_counter() - started) * 1000)
            if not text.strip():
                return Completion(text="", brain_id=self.id, latency_ms=ms, ok=False, error="empty model content")
            return Completion(text=text.strip(), brain_id=self.id, latency_ms=ms, ok=True)
        except Exception as exc:
            ms = int((time.perf_counter() - started) * 1000)
            return Completion(text="", brain_id=self.id, latency_ms=ms, ok=False, error=str(exc))

    def _native_root(self) -> str:
        base = self.endpoint.rstrip("/")
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        return base.rstrip("/") or "http://127.0.0.1:11434"
