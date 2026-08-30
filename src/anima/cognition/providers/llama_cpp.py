"""llama.cpp server is OpenAI-compatible at /v1."""

from __future__ import annotations

from anima.cognition.providers.openai_compatible import OpenAICompatibleBrain


class LlamaCppBrain(OpenAICompatibleBrain):
    def __init__(self, brain_id: str, endpoint: str = "http://127.0.0.1:8080/v1", model: str = "local") -> None:
        super().__init__(brain_id, endpoint, model)
