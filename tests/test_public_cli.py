"""Public CLI verbs: setup, doctor, slash one-shot."""

from __future__ import annotations

from pathlib import Path

from anima.app.cli import main
from anima.app.setup import doctor_report, run_setup
from anima.config.schema import AnimaConfig


def test_setup_noninteractive(data_dir: Path) -> None:
    code = run_setup(data_dir, yes=True, brain="fake")
    assert code == 0
    assert (data_dir / "config.toml").is_file()
    text = (data_dir / "config.toml").read_text(encoding="utf-8")
    assert "instinct" in text
    assert "sibyl_db" in text


def test_doctor_reports_sibyl_and_instinct(cfg: AnimaConfig) -> None:
    rows = {row["name"]: row for row in doctor_report(cfg)}
    assert rows["instinct brain"]["ok"] is True
    assert rows["mainnet locked"]["ok"] is True
    assert rows["sibyl path"]["ok"] is True


def test_cli_setup_yes_after_verb(data_dir: Path) -> None:
    code = main(["setup", "--yes", "--brain", "fake", "--data", str(data_dir)])
    assert code == 0
    assert (data_dir / "config.toml").is_file()


def test_cli_status_once(data_dir: Path) -> None:
    code = main(["--data", str(data_dir), "--brain", "fake", "/status"])
    assert code == 0
