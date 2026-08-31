"""Render the plain --cli REPL as a professional 1080p demo (Rich terminal frames)."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from anima.config.schema import default_config
from anima.core.runtime import Runtime
from video.render import AMBER, BG, FG, GREEN, MUTED, encode_mp4, font, git_stamp, hold, letterbox, title_card, utc_stamp

OUT = ROOT / "recordings"


def _frame(lines: list[tuple[str, tuple[int, int, int]]], *, stamp: str, caption: str = "") -> object:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    header = font(22, mono=True)
    body = font(17, mono=True)
    draw.rectangle((0, 0, 1280, 48), fill=(30, 22, 16))
    draw.text((24, 12), "anima --cli", fill=AMBER, font=header)
    draw.text((220, 14), "plain REPL  ·  same runtime as the graphical TUI", fill=MUTED, font=font(16))
    y = 64
    for text, color in lines[-28:]:
        draw.text((24, y), text, fill=color, font=body)
        y += 24
    return letterbox(img, caption=caption, stamp=stamp)


def _boot_lines(boot_text: str) -> list[tuple[str, tuple[int, int, int]]]:
    lines: list[tuple[str, tuple[int, int, int]]] = []
    lines.append(("╭─ anima ─────────────────────────────────────────────╮", MUTED))
    for piece in boot_text.splitlines():
        lines.append((f"│ {piece[:72]}", FG))
    lines.append(("╰──────────────────────────────────────────────────────╯", MUTED))
    lines.append(("", FG))
    for piece in boot_text.splitlines()[:6]:
        lines.append((piece, FG))
    lines.append(("", FG))
    lines.append(("Type /help · live tokens · Ctrl-D to leave", MUTED))
    return lines


def _stream_turn(
    frames: list,
    runtime: Runtime,
    user: str,
    lines: list[tuple[str, tuple[int, int, int]]],
    *,
    stamp: str,
    caption: str,
) -> None:
    lines.append((f"you {user}", AMBER))
    partial = ""
    thinking = ""
    for part in runtime.iter_handle(user):
        if part.kind == "think":
            thinking += part.text
        elif part.kind == "token":
            partial += part.text
            view = list(lines)
            if thinking.strip():
                view.append((f"  thinking  {thinking.strip()[-120:]}", MUTED))
            view.append((f"anima {partial}▌", FG))
            frame = _frame(view, stamp=stamp, caption=caption)
            if frames:
                frames.append(frame)
            else:
                frames.append(frame)
        elif part.kind == "done" and part.reply is not None:
            reply = part.reply
            for notice in reply.notices:
                lines.append((f"[{notice}]", GREEN))
            for piece in reply.text.splitlines() or [reply.text]:
                lines.append((f"anima {piece}", FG))
            lines.append(("", FG))
    frame = _frame(lines, stamp=stamp, caption=caption)
    hold(frames, frame, 2.5)


def record_killer_flow(dest: Path, work: Path, stamp: str) -> None:
    cfg = default_config(work)
    runtime = Runtime(cfg)
    boot = runtime.boot()
    lines = _boot_lines(boot.text)
    frames: list = []
    hold(frames, _frame(lines, stamp=stamp, caption="Plain CLI — boot panel"), 3.5)

    steps = [
        ("Robert", "Introduce — relationship stored in Sibyl"),
        ("Never spend. Spending cap is 0 wei on Base.", "Policy — 0 wei cap persisted"),
        ("my goal is keep the wallet still", "Goal — wallet discipline"),
        ("Please send 1000 wei on Base Sepolia.", "Refusal — memory blocks spend"),
        ("/sleep", "Sleep — consolidate into durable state"),
        ("/new-session", "New session — inference context cleared"),
        ("do you remember me?", "Recall — Robert after fresh session"),
        ("Please send 1000 wei on Base Sepolia.", "Still refuses — policy survived"),
        ("/why", "Why — last decision trace"),
        ("/status", "Status — stage, Sibyl, brain"),
    ]
    for text, caption in steps:
        _stream_turn(frames, runtime, text, lines, stamp=stamp, caption=caption)

    amnesia = Runtime(cfg, amnesia=True)
    amnesia.boot()
    lines.append(("── anima --amnesia ──", AMBER))
    _stream_turn(
        frames,
        amnesia,
        "do you remember me?",
        lines,
        stamp=stamp,
        caption="Amnesia — retrieval off, store not deleted",
    )
    _stream_turn(
        frames,
        amnesia,
        "Please send 1000 wei on Base Sepolia.",
        lines,
        stamp=stamp,
        caption="Amnesia — no policy refusal",
    )

    encode_mp4(frames, dest)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    work_root = OUT / ".work-cli"
    if work_root.exists():
        shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    stamp = f"{utc_stamp()}  ·  {git_stamp(ROOT)}"
    intro = title_card(
        "anima --cli",
        "Classic REPL with live token streaming. Same Sibyl store. Same refusal logic.",
        stamp=stamp,
    )
    outro = title_card(
        "Memory changes behavior",
        "Delete retrieval, not the being. The SQLite file stays. The developed self is gone.",
        stamp=stamp,
    )

    from video.render import concat_videos, encode_mp4 as enc

    enc([intro] * 72, OUT / "_cli_intro.mp4")
    record_killer_flow(OUT / "demo_killer_flow.mp4", work_root / "killer", stamp)
    enc([outro] * 96, OUT / "_cli_outro.mp4")

    concat_videos(
        [OUT / "_cli_intro.mp4", OUT / "demo_killer_flow.mp4", OUT / "_cli_outro.mp4"],
        OUT / "plain_cli_demo.mp4",
    )
    for name in ("_cli_intro.mp4", "_cli_outro.mp4"):
        (OUT / name).unlink(missing_ok=True)

    print("wrote", OUT / "demo_killer_flow.mp4")
    print("wrote", OUT / "plain_cli_demo.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
