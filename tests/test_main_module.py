"""CLI module entry."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_m_anima_help() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "anima", "--help"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "local-first persistent AI being" in proc.stdout
