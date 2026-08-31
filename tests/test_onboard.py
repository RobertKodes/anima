"""Onboarding flow tests."""

from __future__ import annotations

import json
from pathlib import Path

from anima.app.cli import main
from anima.app.onboard import detect_brain_candidates, needs_onboarding, probe_brain, run_onboard
from anima.config.schema import config_exists, load_config


def test_detect_includes_instinct() -> None:
    providers = {item.provider for item in detect_brain_candidates()}
    assert "fake" in providers


def test_probe_instinct() -> None:
    instinct = next(item for item in detect_brain_candidates() if item.provider == "fake")
    result = probe_brain(instinct, skip=True)
    assert result["ok"] is True


def test_onboard_noninteractive(data_dir: Path) -> None:
    code = run_onboard(data_dir, non_interactive=True, brain="fake", skip_probe=True)
    assert code == 0
    assert config_exists(data_dir=data_dir)
    cfg = load_config(data_dir=data_dir)
    assert cfg.primary_brain_id == "instinct"


def test_onboard_json(data_dir: Path) -> None:
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = run_onboard(data_dir, non_interactive=True, brain="fake", skip_probe=True, json_output=True)
    assert code == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["primary_brain_id"] == "instinct"


def test_cli_onboard_yes(data_dir: Path) -> None:
    code = main(["onboard", "--yes", "--brain", "fake", "--skip-probe", "--data", str(data_dir)])
    assert code == 0
    assert (data_dir / "config.toml").is_file()


def test_needs_onboarding(data_dir: Path) -> None:
    assert needs_onboarding(data_dir) is True
    run_onboard(data_dir, non_interactive=True, brain="fake", skip_probe=True)
    assert needs_onboarding(data_dir) is False
