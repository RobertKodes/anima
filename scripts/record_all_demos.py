#!/usr/bin/env python3
"""Generate all professional demo videos (TUI + plain CLI + judge cut)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> None:
    path = ROOT / "scripts" / script
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, str(path)], check=True, cwd=ROOT)


def main() -> int:
    run("record_cli_videos.py")
    run("record_plain_cli.py")
    run("assemble_hackathon_demo.py")
    print("\nDone. Upload recordings/hackathon_demo.mp4 or recordings/recall_beat.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
