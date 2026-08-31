"""Installer script smoke checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_install_sh_dry_run() -> None:
    if sys.platform == "win32":
        return
    script = ROOT / "install" / "install.sh"
    proc = subprocess.run(["bash", str(script), "--dry-run"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "dry-run" in proc.stdout.lower()


def test_install_ps1_dry_run() -> None:
    if sys.platform != "win32":
        return
    script = ROOT / "install" / "install.ps1"
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-DryRun"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "dry-run" in proc.stdout.lower()
