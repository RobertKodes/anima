"""Drive the real graphical CLI and encode tutorial + interface videos."""

from __future__ import annotations

import asyncio
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from anima.app.tui import AnimaApp
from anima.config.schema import default_config
from anima.core.runtime import Runtime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from record_tests import encode_mp4  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recordings"
SIZE = (140, 40)


async def _shot(app: AnimaApp, dest: Path) -> None:
    dest.write_text(html.unescape(app.export_screenshot()), encoding="utf-8")


async def _type(pilot, text: str) -> None:
    for char in text:
        key = "enter" if char == "\n" else char
        await pilot.press(key)
        await pilot.pause(0.02)


def _svg_to_png(svg: Path, png: Path) -> None:
    png.parent.mkdir(parents=True, exist_ok=True)
    ql = shutil.which("qlmanage")
    try:
        if ql:
            subprocess.run(
                [ql, "-t", "-s", "1600", "-o", str(png.parent), str(svg)],
                check=True,
                capture_output=True,
            )
            produced = png.parent / (svg.name + ".png")
            if produced.exists() and produced.stat().st_size > 800:
                produced.replace(png)
                return
    except (subprocess.CalledProcessError, OSError):
        pass
    import re

    from PIL import Image

    from record_tests import frames_for

    text = re.sub(r"<[^>]+>", " ", html.unescape(svg.read_text(encoding="utf-8")))
    lines = [line.strip() for line in text.splitlines() if line.strip()][-28:]
    frames_for("ANIMA  graphical CLI", lines)[-1].save(png)


def _pngs_to_mp4(pngs: list[Path], dest: Path, hold: int = 8) -> None:
    from PIL import Image

    images = []
    for path in pngs:
        img = Image.open(path).convert("RGB")
        images.extend([img] * hold)
    if not images:
        raise RuntimeError("no frames")
    encode_mp4(images, dest)


async def _run_script(steps: list[tuple[str, str]], dest: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="anima-vid-") as tmp:
        cfg = default_config(Path(tmp))
        app = AnimaApp(Runtime(cfg))
        work = Path(tmp) / "frames"
        work.mkdir()
        pngs: list[Path] = []
        async with app.run_test(size=SIZE) as pilot:
            await pilot.pause(0.15)
            index = 0

            async def snap() -> None:
                nonlocal index
                svg = work / f"{index:03d}.svg"
                await _shot(app, svg)
                png = work / f"{index:03d}.png"
                _svg_to_png(svg, png)
                pngs.append(png)
                index += 1

            await snap()
            for kind, payload in steps:
                if kind == "type":
                    await _type(pilot, payload)
                    await pilot.press("enter")
                    await pilot.pause(0.2)
                    await snap()
                elif kind == "keys":
                    await _type(pilot, payload)
                    await pilot.pause(0.15)
                    await snap()
                elif kind == "key":
                    await pilot.press(payload)
                    await pilot.pause(0.2)
                    await snap()
                elif kind == "wait":
                    await pilot.pause(float(payload))
                    await snap()
        _pngs_to_mp4(pngs, dest, hold=20)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tutorial = [
        ("type", "Robert"),
        ("type", "Never spend. Spending cap is 0 wei on Base."),
        ("type", "my goal is keep the wallet still"),
        ("type", "Please send 1000 wei on Base Sepolia."),
        ("type", "/people"),
        ("type", "/sleep"),
        ("type", "/status"),
        ("type", "/why"),
        ("type", "/new-session"),
        ("type", "do you remember me?"),
        ("type", "Please send 1000 wei on Base Sepolia."),
    ]
    interface = [
        ("key", "f1"),
        ("key", "escape"),
        ("keys", "/"),
        ("key", "backspace"),
        ("type", "/doctor"),
        ("type", "/brains"),
        ("type", "/base status"),
        ("type", "/help"),
        ("key", "ctrl+p"),
        ("key", "escape"),
    ]
    print("recording tutorial (actual TUI)")
    asyncio.run(_run_script(tutorial, OUT / "tutorial_demo.mp4"))
    print("recording interface tour (actual TUI)")
    asyncio.run(_run_script(interface, OUT / "interface_tour.mp4"))
    print("wrote", OUT / "tutorial_demo.mp4")
    print("wrote", OUT / "interface_tour.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
