"""Brain credentials live here — never in Sibyl, never in config.toml plaintext."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

AuthMode = Literal["none", "api_key", "oauth", "env"]


def brain_secret_path(data_dir: Path, brain_id: str) -> Path:
    return data_dir / "secrets" / "brains" / f"{brain_id}.json"


def save_brain_secret(
    data_dir: Path,
    brain_id: str,
    auth_mode: AuthMode,
    *,
    api_key: str = "",
    access_token: str = "",
    refresh_token: str = "",
) -> Path:
    path = brain_secret_path(data_dir, brain_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"auth_mode": auth_mode}
    if auth_mode == "api_key":
        payload["api_key"] = api_key
    elif auth_mode == "oauth":
        payload["access_token"] = access_token
        if refresh_token:
            payload["refresh_token"] = refresh_token
    path.write_text(json.dumps(payload), encoding="utf-8")
    _secure_file(path)
    return path


def load_brain_secret(data_dir: Path, brain_id: str) -> dict[str, Any] | None:
    path = brain_secret_path(data_dir, brain_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def resolve_bearer_token(data_dir: Path, brain_id: str, auth_mode: AuthMode, env_var: str = "") -> str | None:
    if auth_mode == "env" and env_var:
        return os.environ.get(env_var) or None
    secret = load_brain_secret(data_dir, brain_id)
    if not secret:
        return None
    if auth_mode == "api_key":
        return secret.get("api_key") or None
    if auth_mode == "oauth":
        return secret.get("access_token") or secret.get("api_key") or None
    return None


def secret_configured(data_dir: Path, brain_id: str, auth_mode: AuthMode, env_var: str = "") -> bool:
    if auth_mode in {"none", ""}:
        return True
    if auth_mode == "env":
        return bool(env_var and os.environ.get(env_var))
    return load_brain_secret(data_dir, brain_id) is not None


def channel_secret_path(data_dir: Path, kind: str) -> Path:
    return data_dir / "secrets" / "channels" / f"{kind}.json"


def save_channel_token(data_dir: Path, kind: str, token: str) -> Path:
    path = channel_secret_path(data_dir, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": token}), encoding="utf-8")
    _secure_file(path)
    return path


def resolve_channel_token(cfg, kind: str) -> str | None:
    env_map = {"telegram": "TELEGRAM_BOT_TOKEN", "discord": "DISCORD_BOT_TOKEN"}
    env_key = env_map.get(kind)
    if env_key and os.environ.get(env_key):
        return os.environ.get(env_key)
    path = channel_secret_path(cfg.data_dir, kind)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data.get("token") if isinstance(data, dict) else None


def _secure_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except (OSError, NotImplementedError):
        pass
