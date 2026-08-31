"""Capability grant tests."""

from __future__ import annotations

from anima.config.schema import AnimaConfig, BrainConfig, BaseChainConfig
from anima.core.runtime import Runtime
from anima.tools.permissions import may


def _runtime(tmp_path) -> Runtime:
    cfg = AnimaConfig(
        data_dir=tmp_path,
        sibyl_db=tmp_path / "memory.db",
        brains=[BrainConfig(id="instinct", role="primary", provider="fake", model="instinct")],
        primary_brain_id="instinct",
        base=BaseChainConfig(wallet_path=str(tmp_path / "wallet.json"), dry_run=True),
        allow_web_fetch=True,
    )
    rt = Runtime(cfg)
    rt.boot()
    return rt


def test_web_fetch_granted(tmp_path) -> None:
    rt = _runtime(tmp_path)
    ok, _ = may(rt.capabilities, "web_fetch")
    assert ok


def test_web_crawl_denied_by_default(tmp_path) -> None:
    rt = _runtime(tmp_path)
    ok, msg = may(rt.capabilities, "web_crawl")
    assert not ok
