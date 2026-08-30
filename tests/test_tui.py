"""Graphical CLI boots and accepts talk + slash commands in a headless terminal."""

from __future__ import annotations

import asyncio

import html
import re
from anima.app.tui import AnimaApp
from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime


def _drive(cfg: AnimaConfig, keys: list[str]) -> str:
    async def go() -> str:
        app = AnimaApp(Runtime(cfg))
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            for key in keys:
                await pilot.press(key)
            await pilot.pause()
            return html.unescape(app.export_screenshot())

    return asyncio.run(go())


def _visible(svg: str) -> str:
    return re.sub(r"<[^>]+>", "", svg).replace("\xa0", " ")


def test_tui_birth_banner(cfg: AnimaConfig) -> None:
    text = _visible(_drive(cfg, []))
    assert "ANIMA" in text or "A N I M A" in text
    assert "Sibyl" in text or "sibyl" in text.lower()
    assert "awake" in text.lower() or "who are you" in text.lower()


def test_tui_relationship_and_status(cfg: AnimaConfig) -> None:
    keys = list("Robert") + ["enter"]
    svg = _drive(cfg, keys)
    assert "Robert" in svg
    assert "first person" in svg.lower() or "remember" in svg.lower()


def test_tui_slash_help(cfg: AnimaConfig) -> None:
    keys = list("/help") + ["enter"]
    svg = _drive(cfg, keys)
    assert "/status" in svg or "status" in svg.lower()
    assert "/sleep" in svg or "sleep" in svg.lower()
