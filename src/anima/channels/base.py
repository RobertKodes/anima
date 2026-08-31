"""Shared channel adapter interface."""

from __future__ import annotations

from typing import Protocol

from anima.core.events import Reply
from anima.core.runtime import Runtime


class ChannelAdapter(Protocol):
    name: str

    def run(self, runtime: Runtime) -> None:
        ...

    def format_reply(self, reply: Reply) -> str:
        ...


def plain_reply(reply: Reply) -> str:
    parts: list[str] = []
    for notice in reply.notices:
        parts.append(f"[{notice}]")
    parts.append(reply.text)
    return "\n".join(parts)
