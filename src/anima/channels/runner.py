"""Start a chat channel adapter."""

from __future__ import annotations

from anima.channels.discord import DiscordChannel
from anima.channels.telegram import TelegramChannel
from anima.core.runtime import Runtime

CHANNELS = {
    "telegram": TelegramChannel,
    "discord": DiscordChannel,
}


def run_channel(runtime: Runtime, kind: str) -> None:
    cls = CHANNELS.get(kind)
    if cls is None:
        known = ", ".join(sorted(CHANNELS))
        raise ValueError(f"unknown channel {kind!r}; known: {known}")
    adapter = cls(runtime)
    adapter.run(runtime)
