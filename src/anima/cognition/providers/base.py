from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Completion:
    text: str
    brain_id: str
    latency_ms: int = 0
    ok: bool = True
    error: str = ""


@dataclass
class StreamChunk:
    kind: str  # "think" | "token"
    text: str


class Brain(Protocol):
    id: str
    model: str

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 400) -> Completion: ...

    def health(self) -> dict: ...


def stream_brain(
    brain: object,
    prompt: str,
    *,
    system: str = "",
    max_tokens: int = 400,
) -> Iterator[StreamChunk]:
    """Stream tokens when supported; otherwise emit the full reply once."""
    stream = getattr(brain, "stream_complete", None)
    if callable(stream):
        yield from stream(prompt, system=system, max_tokens=max_tokens)
        return
    result = brain.complete(prompt, system=system, max_tokens=max_tokens)  # type: ignore[attr-defined]
    if result.text:
        yield StreamChunk("token", result.text)
