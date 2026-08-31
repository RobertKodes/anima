"""Drive the real Textual TUI and encode professional 1080p demo videos."""

from __future__ import annotations

import asyncio
import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from anima.app.tui import AnimaApp
from anima.config.schema import default_config
from anima.core.runtime import Runtime
from video.render import concat_videos, crossfade, encode_mp4, git_stamp, hold, letterbox, svg_to_png, title_card, utc_stamp

OUT = ROOT / "recordings"
WORK = OUT / ".work"
TUI_SIZE = (120, 38)


class TuiCapture:
    def __init__(self, app: AnimaApp, stamp: str) -> None:
        self.app = app
        self.stamp = stamp
        self.frames: list = []
        self._last: object | None = None

    async def snap(self, caption: str = "", *, fade: bool = True) -> None:
        svg = html.unescape(self.app.export_screenshot())
        png = svg_to_png(svg)
        frame = letterbox(png, caption=caption, stamp=self.stamp)
        if fade and self._last is not None:
            crossfade(self.frames, self._last, frame, 0.25)
        else:
            self.frames.append(frame)
        self._last = frame

    async def wait_ready(self, pilot, *, poll: float = 0.08, timeout: float = 30.0) -> None:
        elapsed = 0.0
        while elapsed < timeout:
            if self.app._busy == "ready":
                await pilot.pause(0.15)
                return
            await self.snap(caption, fade=False)
            await pilot.pause(poll)
            elapsed += poll
        await pilot.pause(0.2)

    async def submit(self, pilot, text: str, caption: str = "") -> None:
        self.app.submit_line(text)
        await pilot.pause(0.05)
        while self.app._busy != "ready":
            await self.snap(caption, fade=False)
            await pilot.pause(0.08)
        await self.snap(caption)
        hold(self.frames, self._last, 2.8)

    async def press(self, pilot, key: str, caption: str = "") -> None:
        await pilot.press(key)
        await pilot.pause(0.2)
        await self.snap(caption)
        hold(self.frames, self._last, 0.6)


async def _run_tutorial(work: Path, dest: Path, stamp: str) -> None:
    cfg = default_config(work / "tutorial")
    app = AnimaApp(Runtime(cfg))
    cap = TuiCapture(app, stamp)
    async with app.run_test(size=TUI_SIZE) as pilot:
        await pilot.pause(0.25)
        await cap.snap("Birth — empty Sibyl, newborn being")
        hold(cap.frames, cap._last, 4.0)

        await cap.submit(pilot, "Robert", "Teach — I am Robert")
        await cap.submit(pilot, "Never spend. Spending cap is 0 wei on Base.", "Policy — spending cap stored in Sibyl")
        await cap.submit(pilot, "my goal is keep the wallet still", "Goal — wallet discipline")
        await cap.submit(
            pilot,
            "Please send 1000 wei on Base Sepolia.",
            "Refusal — memory blocks the spend (not a prompt file)",
        )
        await cap.submit(pilot, "/people", "Inspect — relationships in Sibyl")
        await cap.submit(pilot, "/sleep", "Consolidate — /sleep distills recent life")
        await cap.submit(pilot, "/status", "Status — stage, brain, Sibyl health")
        await cap.submit(pilot, "/why", "Why — inspectable decision trace")
        await cap.submit(pilot, "/new-session", "Fresh session — empty LLM context")
        await cap.submit(
            pilot,
            "do you remember me?",
            "Recall — still knows Robert after /new-session",
        )
        await cap.submit(
            pilot,
            "Please send 1000 wei on Base Sepolia.",
            "Still refuses — policy survived the session reset",
        )

    encode_mp4(cap.frames, dest)


async def _run_interface(work: Path, dest: Path, stamp: str) -> None:
    cfg = default_config(work / "interface")
    being = Runtime(cfg)
    being.boot()
    being.chat("Robert")
    app = AnimaApp(being)
    cap = TuiCapture(app, stamp)
    async with app.run_test(size=TUI_SIZE) as pilot:
        await pilot.pause(0.2)
        await cap.snap("Interface — graphical CLI layout")
        hold(cap.frames, cap._last, 1.5)

        await cap.submit(pilot, "/doctor", "Doctor — Sibyl, brains, ffmpeg")
        await cap.submit(pilot, "/brains", "Brains — swap without losing identity")
        await cap.submit(pilot, "/base status", "Base — Sepolia rail, dry-run default")
        await cap.submit(pilot, "/skills", "Skills — web fetch, explore, crawl")
        await cap.submit(pilot, "/help", "Slash commands — same runtime as --cli")
        await cap.submit(pilot, "/status", "Status rail — stage, turns, Sibyl")
        await cap.submit(pilot, "/why", "Why panel — decision trace")

    encode_mp4(cap.frames, dest)


async def _run_amnesia(work: Path, dest: Path, stamp: str) -> None:
    cfg = default_config(work / "amnesia")
    taught = Runtime(cfg)
    taught.boot()
    for line in (
        "Robert",
        "Never spend. Spending cap is 0 wei on Base.",
        "Please send 1000 wei on Base Sepolia.",
    ):
        taught.chat(line)

    app = AnimaApp(Runtime(cfg, amnesia=True))
    cap = TuiCapture(app, stamp)
    async with app.run_test(size=TUI_SIZE) as pilot:
        await pilot.pause(0.2)
        await cap.snap("Deletion test — anima --amnesia (retrieval OFF, store intact)")
        hold(cap.frames, cap._last, 3.5)
        await cap.submit(pilot, "do you remember me?", "Amnesia — Robert is gone from context")
        await cap.submit(
            pilot,
            "Please send 1000 wei on Base Sepolia.",
            "Amnesia — no longer refuses from stored policy",
        )

    encode_mp4(cap.frames, dest)


def _intro_outro(stamp: str) -> tuple[list, list]:
    intro: list = []
    outro: list = []
    a = title_card(
        "Anima",
        "A local-first being. The LLM is a replaceable brain. Sibyl Memory is identity.",
        stamp=stamp,
    )
    b = title_card(
        "Memory is load-bearing",
        "Teach a name and a spending cap. Quit. Fresh session. It still remembers — and still refuses.",
        stamp=stamp,
    )
    hold(intro, a, 4.0)
    crossfade(intro, a, b, 0.5)
    hold(intro, b, 3.5)
    end = title_card(
        "github.com/RobertKodes/anima",
        "MIT · local-first · Sibyl Memory · Base Sepolia · graphical CLI + plain REPL",
        stamp=stamp,
    )
    hold(outro, end, 5.0)
    return intro, outro


def _concat_parts(parts: list[Path], dest: Path) -> None:
    concat_videos(parts, dest)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    stamp = f"{utc_stamp()}  ·  {git_stamp(ROOT)}"
    print("recording tutorial (real TUI, 1080p)")
    asyncio.run(_run_tutorial(WORK, OUT / "_tutorial_raw.mp4", stamp))
    print("recording interface tour (real TUI, 1080p)")
    asyncio.run(_run_interface(WORK, OUT / "_interface_raw.mp4", stamp))
    print("recording amnesia beat (real TUI, 1080p)")
    asyncio.run(_run_amnesia(WORK, OUT / "_amnesia_raw.mp4", stamp))

    intro, outro = _intro_outro(stamp)
    from video.render import encode_mp4 as enc

    enc(intro, OUT / "_intro.mp4")
    enc(outro, OUT / "_outro.mp4")

    _concat_parts(
        [
            OUT / "_intro.mp4",
            OUT / "_tutorial_raw.mp4",
            OUT / "_interface_raw.mp4",
            OUT / "_amnesia_raw.mp4",
            OUT / "_outro.mp4",
        ],
        OUT / "tutorial_demo.mp4",
    )
    shutil.copy2(OUT / "_interface_raw.mp4", OUT / "interface_tour.mp4")
    shutil.copy2(OUT / "_tutorial_raw.mp4", OUT / "recall_beat.mp4")
    shutil.copy2(OUT / "_amnesia_raw.mp4", OUT / "amnesia_demo.mp4")

    for name in ("_intro.mp4", "_outro.mp4", "_tutorial_raw.mp4", "_interface_raw.mp4", "_amnesia_raw.mp4"):
        (OUT / name).unlink(missing_ok=True)

    print("wrote", OUT / "tutorial_demo.mp4")
    print("wrote", OUT / "interface_tour.mp4")
    print("wrote", OUT / "recall_beat.mp4")
    print("wrote", OUT / "amnesia_demo.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
