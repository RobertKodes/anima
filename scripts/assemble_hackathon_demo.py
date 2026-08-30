#!/usr/bin/env python3
"""Assemble a 2–5 minute judge cut with a burned-in timestamp (and optional commit hash)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "recordings"
FPS = 8
W, H = 1600, 900
BG = (13, 11, 18)
FG = (244, 234, 220)
AMBER = (232, 160, 74)
MUTED = (160, 148, 132)


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _git_stamp() -> str:
    try:
        short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if short and "fatal" not in short:
            return short
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "uncommitted"


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def card(title: str, body: str, stamp: str, seconds: int) -> list[Image.Image]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    title_font = _font(54)
    body_font = _font(32)
    stamp_font = _font(22)
    draw.text((48, 36), stamp, fill=AMBER, font=stamp_font)
    draw.text((48, 220), title, fill=AMBER, font=title_font)
    y = 320
    for line in _wrap(draw, body, body_font, W - 96):
        draw.text((48, y), line, fill=FG, font=body_font)
        y += 46
    draw.text((48, H - 64), "Anima  ·  Sibyl is the self  ·  Base is the rail", fill=MUTED, font=stamp_font)
    return [img] * (seconds * FPS)


def _probe(path: Path) -> tuple[int, int, float]:
    def field(key: str) -> str:
        return subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                key,
                "-of",
                "csv=p=0",
                str(path),
            ],
            text=True,
        ).strip()

    w, h = field("stream=width,height").split(",")
    duration = float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            text=True,
        ).strip()
    )
    return int(w), int(h), duration


def _letterbox(src: Path, dest: Path, stamp: str) -> None:
    scale = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0d0b12"
    )
    font = "/System/Library/Fonts/Supplemental/Arial.ttf"
    if not Path(font).exists():
        font = "/System/Library/Fonts/Helvetica.ttc"
    draw = (
        f"{scale},drawtext=fontfile={font}:text='{stamp}':"
        "x=24:y=24:fontsize=22:fontcolor=0xe8a04a:"
        "box=1:boxcolor=0x0d0b12@0.75:boxborderw=8"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        draw,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        cmd[cmd.index("-vf") + 1] = scale
        subprocess.run(cmd, check=True, capture_output=True)


def _encode_cards(frames: list[Image.Image], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="anima-cards-") as tmp:
        dir_ = Path(tmp)
        for i, frame in enumerate(frames):
            frame.save(dir_ / f"{i:05d}.png")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(dir_ / "%05d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )


def main() -> int:
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stamp = f"{utc}  ·  Anima  ·  { _git_stamp() }"
    # drawtext cannot have colons in some builds if they confuse the filter parser.
    stamp_safe = stamp.replace(":", "-").replace("'", "")

    clips = [
        ("The problem", "People want a local being that still knows them tomorrow. Chatbots forget. Markdown identity files are not a self — they are notes the model might read."),
        ("Who has it", "Builders who live in a terminal and will not upload their life to a cloud agent. Hackathon judges who must see memory change a decision, not decorate a prompt."),
        ("The product", "Anima. Graphical CLI. The LLM is a replaceable brain. Sibyl Memory (SQLite + FTS5) is identity. Base Sepolia is the action rail. Keys never enter Sibyl."),
        ("How it works", "Retrieve a small context package before every reply. Persist experience after. Sleep consolidates. /new-session clears the model context and leaves Sibyl untouched."),
    ]
    after = [
        ("Fresh session", "The previous clip is the recall beat: empty inference context, same Sibyl file, the being still knows the person and still refuses the spend."),
        ("Deletion test", "anima --amnesia turns retrieval off. It can still talk. It is no longer the developed being. The SQLite file is not deleted."),
        ("Base", "Default network is Base Sepolia. Dry-run so a clone cannot spend. A remembered 0-wei cap blocks execute. A live broadcast is optional and needs a funded wallet."),
        ("Submit", "Public MIT repo. README two-minute path. Two posts tagging @sibylcap and @base. Prefer an unedited live capture of the recall beat for the form."),
    ]

    needed = [
        OUT / "tutorial_demo.mp4",
        OUT / "interface_tour.mp4",
        OUT / "demo_killer_flow.mp4",
    ]
    missing = [p for p in needed if not p.is_file()]
    if missing:
        print("missing source clips:", missing, file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="anima-demo-") as tmp:
        work = Path(tmp)
        parts: list[Path] = []
        n = 0

        def add_cards(items: list[tuple[str, str]], seconds: int = 12) -> None:
            nonlocal n
            frames: list[Image.Image] = []
            for title, body in items:
                frames.extend(card(title, body, stamp, seconds))
            path = work / f"{n:02d}_cards.mp4"
            _encode_cards(frames, path)
            parts.append(path)
            n += 1

        add_cards(clips, 12)
        for src in needed:
            dest = work / f"{n:02d}_{src.stem}.mp4"
            _letterbox(src, dest, stamp_safe)
            parts.append(dest)
            n += 1
        add_cards(after, 10)

        concat = work / "list.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        dest = OUT / "hackathon_demo.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )
        duration = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dest)],
            text=True,
        ).strip()
        print(f"wrote {dest} duration={duration}s stamp={stamp}")
        seconds = float(duration)
        if seconds < 120 or seconds > 300:
            print(f"warning: duration {seconds:.1f}s is outside 2–5 min", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
