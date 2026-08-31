"""Onboard skills configuration."""

from __future__ import annotations

from anima.app.onboard import run_onboard
from anima.config.schema import load_config
from anima.skills.catalog import granted_skills


def test_onboard_auto_enables_web_skills(data_dir) -> None:
    code = run_onboard(data_dir, non_interactive=True, brain="fake", skip_probe=True)
    assert code == 0
    cfg = load_config(data_dir=data_dir)
    enabled = {s.capability for s in granted_skills(cfg)}
    assert "web_fetch" in enabled
    assert "explore" in enabled


def test_onboard_skills_flag(data_dir) -> None:
    code = run_onboard(
        data_dir,
        non_interactive=True,
        brain="fake",
        skip_probe=True,
        skills="web_fetch,web_crawl",
    )
    assert code == 0
    cfg = load_config(data_dir=data_dir)
    assert cfg.allow_web_fetch
    assert cfg.allow_web_crawl
    assert not cfg.allow_explore
