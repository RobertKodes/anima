from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Completion:
    text: str
    brain_id: str
    latency_ms: int = 0
    ok: bool = True
    error: str = ""


class Brain(Protocol):
    id: str
    model: str

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 400) -> Completion: ...

    def health(self) -> dict: ...
