"""Cloud and API auth for brains."""

from __future__ import annotations

import json
from pathlib import Path

from anima.app.onboard import _build_cloud_candidate, candidate_to_config, probe_brain
from anima.cognition.cloud import auth_headers, brain_config_from_cloud
from anima.config.secrets import load_brain_secret, resolve_bearer_token, save_brain_secret


def test_brain_config_from_cloud_openai() -> None:
    cfg = brain_config_from_cloud("openai", auth_mode="env")
    assert cfg.provider == "openai_compatible"
    assert cfg.endpoint.startswith("https://")
    assert cfg.auth_mode == "env"
    assert cfg.env_var == "OPENAI_API_KEY"


def test_save_and_load_api_key(data_dir: Path) -> None:
    save_brain_secret(data_dir, "openai-cloud", "api_key", api_key="sk-test")
    secret = load_brain_secret(data_dir, "openai-cloud")
    assert secret is not None
    assert secret["api_key"] == "sk-test"
    assert resolve_bearer_token(data_dir, "openai-cloud", "api_key") == "sk-test"


def test_auth_headers_from_env(data_dir: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    cfg = brain_config_from_cloud("openai", auth_mode="env")
    headers = auth_headers(cfg, data_dir)
    assert headers["Authorization"] == "Bearer sk-env"


def test_cloud_candidate_probe_skipped(data_dir: Path) -> None:
    save_brain_secret(data_dir, "openai-cloud", "api_key", api_key="sk-test")
    candidate = _build_cloud_candidate(
        data_dir,
        "openai",
        auth="api_key",
        api_key="sk-test",
    )
    cfg = candidate_to_config(candidate)
    assert cfg.cost_class == "cloud"
    result = probe_brain(candidate, data_dir=data_dir, skip=True)
    assert result["ok"] is True


def test_onboard_cloud_env_noninteractive(data_dir: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    from anima.app.onboard import run_onboard

    code = run_onboard(
        data_dir,
        non_interactive=True,
        cloud="openai",
        auth="env",
        skip_probe=True,
    )
    assert code == 0
    secret_path = data_dir / "secrets" / "brains" / "openai-cloud.json"
    assert not secret_path.exists()
