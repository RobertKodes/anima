from __future__ import annotations

from pathlib import Path

import pytest

from anima.config.schema import AnimaConfig, BaseChainConfig, BrainConfig, default_config
from anima.core.runtime import Runtime


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "anima-life"


@pytest.fixture
def cfg(data_dir: Path) -> AnimaConfig:
    cfg = default_config(data_dir)
    cfg.brains = [
        BrainConfig(id="instinct", role="primary", provider="fake", model="instinct", capabilities=["conversation"])
    ]
    cfg.primary_brain_id = "instinct"
    cfg.base = BaseChainConfig(
        wallet_path=str(data_dir / "secrets" / "wallet.json"),
        dry_run=True,
        approval_mode="always-ask",
        per_action_limit_wei=0,
    )
    return cfg


@pytest.fixture
def runtime(cfg: AnimaConfig) -> Runtime:
    being = Runtime(cfg)
    being.boot()
    return being
