"""Cloud brain presets and auth resolution for OpenAI-compatible APIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from anima.config.schema import BrainConfig
from anima.config.secrets import resolve_bearer_token

AuthChoice = Literal["api_key", "oauth", "env"]


@dataclass(frozen=True)
class CloudPreset:
    id: str
    label: str
    endpoint: str
    default_model: str
    env_var: str
    oauth_url: str = ""
    brain_id: str = ""


CLOUD_PRESETS: dict[str, CloudPreset] = {
    "openai": CloudPreset(
        id="openai",
        label="OpenAI",
        endpoint="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        env_var="OPENAI_API_KEY",
        oauth_url="https://platform.openai.com/api-keys",
        brain_id="openai-cloud",
    ),
    "openrouter": CloudPreset(
        id="openrouter",
        label="OpenRouter",
        endpoint="https://openrouter.ai/api/v1",
        default_model="openrouter/auto",
        env_var="OPENROUTER_API_KEY",
        oauth_url="https://openrouter.ai/keys",
        brain_id="openrouter-cloud",
    ),
    "groq": CloudPreset(
        id="groq",
        label="Groq",
        endpoint="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        env_var="GROQ_API_KEY",
        oauth_url="https://console.groq.com/keys",
        brain_id="groq-cloud",
    ),
    "together": CloudPreset(
        id="together",
        label="Together AI",
        endpoint="https://api.together.xyz/v1",
        default_model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        env_var="TOGETHER_API_KEY",
        oauth_url="https://api.together.ai/settings/api-keys",
        brain_id="together-cloud",
    ),
    "custom": CloudPreset(
        id="custom",
        label="Custom OpenAI-compatible",
        endpoint="",
        default_model="",
        env_var="ANIMA_API_KEY",
        brain_id="custom-cloud",
    ),
}


def preset_ids() -> list[str]:
    return list(CLOUD_PRESETS.keys())


def auth_headers(cfg: BrainConfig, data_dir: Path) -> dict[str, str]:
    if cfg.auth_mode in {"none", ""}:
        return {}
    token = resolve_bearer_token(data_dir, cfg.id, cfg.auth_mode, cfg.env_var)
    if not token:
        return {}
    headers = {"Authorization": f"Bearer {token}"}
    if cfg.provider == "openai_compatible" and "openrouter" in cfg.endpoint:
        headers.setdefault("HTTP-Referer", "https://github.com/RobertKodes/anima")
        headers.setdefault("X-Title", "Anima")
    return headers


def brain_config_from_cloud(
    preset_id: str,
    *,
    model: str | None = None,
    endpoint: str | None = None,
    auth_mode: AuthChoice = "api_key",
    env_var: str | None = None,
) -> BrainConfig:
    preset = CLOUD_PRESETS[preset_id]
    resolved_endpoint = endpoint or preset.endpoint
    if not resolved_endpoint:
        raise ValueError("custom cloud preset requires --endpoint")
    resolved_model = model or preset.default_model
    if not resolved_model:
        raise ValueError("custom cloud preset requires --model")
    return BrainConfig(
        id=preset.brain_id if preset_id != "custom" else "custom-cloud",
        role="primary",
        provider="openai_compatible",
        endpoint=resolved_endpoint.rstrip("/"),
        model=resolved_model,
        activation="always",
        cost_class="cloud",
        capabilities=["conversation"],
        auth_mode=auth_mode,
        secret_id=preset.brain_id if preset_id != "custom" else "custom-cloud",
        env_var=env_var or preset.env_var,
    )
