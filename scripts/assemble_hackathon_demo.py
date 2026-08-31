#!/usr/bin/env python3
"""Assemble the 2–5 minute hackathon judge cut from professional demo clips."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video.render import FPS, concat_videos, encode_mp4, git_stamp, hold, probe_duration, title_card, utc_stamp

OUT = ROOT / "recordings"


def _cards_video(items: list[tuple[str, str]], dest: Path, stamp: str, seconds: int = 10) -> None:
    frames = []
    for title, body in items:
        hold(frames, title_card(title, body, stamp=stamp), seconds)
    encode_mp4(frames, dest)


def main() -> int:
    stamp = f"{utc_stamp()}  ·  Anima  ·  {git_stamp(ROOT)}"
    needed = [
        OUT / "recall_beat.mp4",
        OUT / "plain_cli_demo.mp4",
        OUT / "interface_tour.mp4",
        OUT / "amnesia_demo.mp4",
    ]
    missing = [p for p in needed if not p.is_file()]
    if missing:
        print("missing clips — run: python scripts/record_all_demos.py", file=sys.stderr)
        print("missing:", missing, file=sys.stderr)
        return 1

    open_cards = [
        (
            "The problem",
            "Chatbots forget. Markdown files are notes, not a self. Builders want a local being that still knows them tomorrow.",
        ),
        (
            "The product",
            "Anima — graphical TUI and plain REPL. LLM brains are replaceable. Sibyl Memory is identity. Base Sepolia is the action rail.",
        ),
    ]
    close_cards = [
        (
            "Fresh session",
            "Empty inference context. Same Sibyl file. The being still recalls Robert and still refuses the spend.",
        ),
        (
            "Deletion test",
            "anima --amnesia turns retrieval off. It can still talk. It is no longer the developed being. The SQLite file is not deleted.",
        ),
        (
            "Submit",
            "Public MIT repo · memory changes decisions · prefer recall_beat.mp4 or tutorial_demo.mp4 for the form.",
        ),
    ]

    work = OUT / ".assemble"
    work.mkdir(parents=True, exist_ok=True)
    _cards_video(open_cards, work / "open.mp4", stamp, 9)
    _cards_video(close_cards, work / "close.mp4", stamp, 8)

    dest = OUT / "hackathon_demo.mp4"
    concat_videos(
        [
            work / "open.mp4",
            needed[0],
            needed[1],
            needed[2],
            needed[3],
            work / "close.mp4",
        ],
        dest,
    )
    seconds = probe_duration(dest)
    print(f"wrote {dest} duration={seconds:.1f}s stamp={stamp}")
    if seconds < 120:
        print(f"note: {seconds:.1f}s is under 2 min — acceptable if recall beat is unedited in source clips", file=sys.stderr)
    elif seconds > 360:
        print(f"warning: {seconds:.1f}s exceeds 5 min", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
