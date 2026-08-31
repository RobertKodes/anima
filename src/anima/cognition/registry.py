from __future__ import annotations

from pathlib import Path

from anima.cognition.cloud import auth_headers
from anima.config.schema import BrainConfig
from anima.cognition.providers.base import Brain
from anima.cognition.providers.fake import InstinctBrain
from anima.cognition.providers.llama_cpp import LlamaCppBrain
from anima.cognition.providers.ollama import OllamaBrain
from anima.cognition.providers.openai_compatible import OpenAICompatibleBrain


class BrainRegistry:
    def __init__(self, configs: list[BrainConfig], primary_id: str = "", *, data_dir: Path | None = None) -> None:
        self.configs = {cfg.id: cfg for cfg in configs}
        self.primary_id = primary_id or (configs[0].id if configs else "instinct")
        self._instances: dict[str, Brain] = {}
        self.data_dir = data_dir

    def list(self) -> list[BrainConfig]:
        return list(self.configs.values())

    def add(self, cfg: BrainConfig) -> None:
        self.configs[cfg.id] = cfg
        self._instances.pop(cfg.id, None)

    def set_primary(self, brain_id: str) -> None:
        if brain_id not in self.configs:
            raise KeyError(brain_id)
        self.primary_id = brain_id

    def get(self, brain_id: str | None = None) -> Brain:
        target = brain_id or self.primary_id
        if target not in self._instances:
            self._instances[target] = build_brain(self.configs[target], self.data_dir)
        return self._instances[target]

    def health(self) -> list[dict]:
        rows = []
        for cfg in self.configs.values():
            brain = self.get(cfg.id)
            info = brain.health()
            info.update({"role": cfg.role, "activation": cfg.activation, "capabilities": cfg.capabilities})
            rows.append(info)
        return rows


def build_brain(cfg: BrainConfig, data_dir: Path | None = None) -> Brain:
    if cfg.provider == "fake":
        return InstinctBrain(cfg.id)
    if cfg.provider == "ollama":
        return OllamaBrain(cfg.id, cfg.endpoint or "http://127.0.0.1:11434/v1", cfg.model or "qwen3:1.7b")
    if cfg.provider == "llama_cpp":
        return LlamaCppBrain(cfg.id, cfg.endpoint or "http://127.0.0.1:8080/v1", cfg.model or "local")
    headers = auth_headers(cfg, data_dir) if data_dir and cfg.auth_mode not in {"none", ""} else {}
    if data_dir and cfg.auth_mode not in {"none", ""} and not headers:
        from anima.config.schema import default_data_dir

        headers = auth_headers(cfg, default_data_dir())
    return OpenAICompatibleBrain(
        cfg.id,
        cfg.endpoint or "http://127.0.0.1:8080/v1",
        cfg.model,
        headers=headers,
    )
