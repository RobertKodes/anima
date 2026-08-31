"""Runtime configuration. Identity does not live here — Sibyl does."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


ApprovalMode = Literal["always-ask", "policy-limited", "disabled"]
ProviderKind = Literal["openai_compatible", "llama_cpp", "ollama", "fake"]
AuthMode = Literal["none", "api_key", "oauth", "env"]


class BrainConfig(BaseModel):
    id: str
    role: str = "primary"
    provider: ProviderKind = "ollama"
    endpoint: str = ""
    model: str = ""
    activation: Literal["always", "on_demand"] = "always"
    max_context: int = 8192
    cost_class: str = "local"
    capabilities: list[str] = Field(default_factory=list)
    auth_mode: AuthMode = "none"
    secret_id: str = ""
    env_var: str = ""


class BaseChainConfig(BaseModel):
    network: str = "sepolia"
    chain_id: int = 84532
    rpc: str = "https://sepolia.base.org"
    approval_mode: ApprovalMode = "always-ask"
    mainnet_enabled: bool = False
    per_action_limit_wei: int = 0
    cumulative_limit_wei: int = 0
    wallet_path: str = ""
    # Dry-run never broadcasts. Tests and first-run use this until a key exists.
    dry_run: bool = True


class McpServerConfig(BaseModel):
    id: str
    title: str = ""
    transport: Literal["stdio"] = "stdio"
    command: str = ""
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    optional: bool = True


class ChannelConfig(BaseModel):
    kind: Literal["telegram", "discord", "web"]
    enabled: bool = False
    note: str = ""


class AnimaConfig(BaseModel):
    data_dir: Path
    sibyl_db: Path
    tenant_id: str = "anima-being"
    brains: list[BrainConfig] = Field(default_factory=list)
    primary_brain_id: str = ""
    base: BaseChainConfig = Field(default_factory=BaseChainConfig)
    allow_shell: bool = False
    allow_web_fetch: bool = False
    allow_web_crawl: bool = False
    allow_explore: bool = False
    active_experience_id: str = ""
    mcp_servers: list[McpServerConfig] = Field(default_factory=list)
    channels: list[ChannelConfig] = Field(default_factory=list)
    log_path: Path | None = None
    amnesia: bool = False

    def primary(self) -> BrainConfig:
        if self.primary_brain_id:
            for brain in self.brains:
                if brain.id == self.primary_brain_id:
                    return brain
        for brain in self.brains:
            if brain.role == "primary":
                return brain
        if self.brains:
            return self.brains[0]
        return BrainConfig(id="instinct", role="primary", provider="fake", model="instinct")


def default_data_dir() -> Path:
    override = os.environ.get("ANIMA_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".anima"


def default_config(data_dir: Path | None = None) -> AnimaConfig:
    root = (data_dir or default_data_dir()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "secrets").mkdir(parents=True, exist_ok=True)
    return AnimaConfig(
        data_dir=root,
        sibyl_db=root / "memory.db",
        tenant_id="anima-being",
        brains=[
            BrainConfig(
                id="instinct",
                role="primary",
                provider="fake",
                model="instinct",
                capabilities=["conversation"],
            )
        ],
        primary_brain_id="instinct",
        base=BaseChainConfig(wallet_path=str(root / "secrets" / "wallet.json"), dry_run=True),
        log_path=root / "anima.log",
    )


def config_exists(path: Path | None = None, data_dir: Path | None = None) -> bool:
    cfg = default_config(data_dir)
    file_path = path or (cfg.data_dir / "config.toml")
    return file_path.is_file()


def load_config(path: Path | None = None, data_dir: Path | None = None) -> AnimaConfig:
    cfg = default_config(data_dir)
    file_path = path or (cfg.data_dir / "config.toml")
    if file_path.is_file():
        raw = tomllib.loads(file_path.read_text(encoding="utf-8"))
        cfg = _merge(cfg, raw)
    if os.environ.get("ANIMA_AMNESIA") == "1":
        cfg.amnesia = True
    return cfg


def save_config(cfg: AnimaConfig, path: Path | None = None) -> Path:
    target = path or (cfg.data_dir / "config.toml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_to_toml(cfg), encoding="utf-8")
    return target


def _merge(cfg: AnimaConfig, raw: dict[str, Any]) -> AnimaConfig:
    data = cfg.model_dump()
    if "data_dir" in raw:
        data["data_dir"] = Path(raw["data_dir"]).expanduser()
    if "sibyl_db" in raw:
        data["sibyl_db"] = Path(raw["sibyl_db"]).expanduser()
    if "tenant_id" in raw:
        data["tenant_id"] = str(raw["tenant_id"])
    if "primary_brain_id" in raw:
        data["primary_brain_id"] = str(raw["primary_brain_id"])
    if "allow_shell" in raw:
        data["allow_shell"] = bool(raw["allow_shell"])
    if "allow_web_fetch" in raw:
        data["allow_web_fetch"] = bool(raw["allow_web_fetch"])
    if "allow_web_crawl" in raw:
        data["allow_web_crawl"] = bool(raw["allow_web_crawl"])
    if "allow_explore" in raw:
        data["allow_explore"] = bool(raw["allow_explore"])
    if "active_experience_id" in raw:
        data["active_experience_id"] = str(raw["active_experience_id"])
    if "amnesia" in raw:
        data["amnesia"] = bool(raw["amnesia"])
    if "log_path" in raw:
        data["log_path"] = Path(raw["log_path"]).expanduser()
    brains = raw.get("brains")
    if isinstance(brains, list) and brains:
        data["brains"] = [BrainConfig.model_validate(item).model_dump() for item in brains]
    base = raw.get("base")
    if isinstance(base, dict):
        merged_base = {**data["base"], **base}
        data["base"] = merged_base
    mcp = raw.get("mcp_servers")
    if isinstance(mcp, list):
        data["mcp_servers"] = [McpServerConfig.model_validate(item).model_dump() for item in mcp]
    channels = raw.get("channels")
    if isinstance(channels, list):
        data["channels"] = [ChannelConfig.model_validate(item).model_dump() for item in channels]
    if data.get("data_dir"):
        data["data_dir"] = Path(data["data_dir"])
    if data.get("sibyl_db"):
        data["sibyl_db"] = Path(data["sibyl_db"])
    if data.get("log_path"):
        data["log_path"] = Path(data["log_path"])
    return AnimaConfig.model_validate(data)


def _toml_path(value: Path | str) -> str:
    return str(value).replace("\\", "/")


def _to_toml(cfg: AnimaConfig) -> str:
    brains = []
    for brain in cfg.brains:
        caps = ", ".join(f'"{c}"' for c in brain.capabilities)
        brains.append(
            "[[brains]]\n"
            f'id = "{brain.id}"\n'
            f'role = "{brain.role}"\n'
            f'provider = "{brain.provider}"\n'
            f'endpoint = "{brain.endpoint}"\n'
            f'model = "{brain.model}"\n'
            f'activation = "{brain.activation}"\n'
            f"max_context = {brain.max_context}\n"
            f'cost_class = "{brain.cost_class}"\n'
            f'auth_mode = "{brain.auth_mode}"\n'
            f'secret_id = "{brain.secret_id or brain.id}"\n'
            f'env_var = "{brain.env_var}"\n'
            f"capabilities = [{caps}]\n"
        )
    base = cfg.base
    mcp_blocks = []
    for server in cfg.mcp_servers:
        args = ", ".join(f'"{a}"' for a in server.args)
        mcp_blocks.append(
            "[[mcp_servers]]\n"
            f'id = "{server.id}"\n'
            f'title = "{server.title}"\n'
            f'transport = "{server.transport}"\n'
            f'command = "{server.command}"\n'
            f"args = [{args}]\n"
            f"enabled = {str(server.enabled).lower()}\n"
            f"optional = {str(server.optional).lower()}\n"
        )
    channel_blocks = []
    for ch in cfg.channels:
        channel_blocks.append(
            "[[channels]]\n"
            f'kind = "{ch.kind}"\n'
            f"enabled = {str(ch.enabled).lower()}\n"
            f'note = "{ch.note}"\n'
        )
    return (
        f'data_dir = "{_toml_path(cfg.data_dir)}"\n'
        f'sibyl_db = "{_toml_path(cfg.sibyl_db)}"\n'
        f'tenant_id = "{cfg.tenant_id}"\n'
        f'primary_brain_id = "{cfg.primary_brain_id}"\n'
        f"allow_shell = {str(cfg.allow_shell).lower()}\n"
        f"allow_web_fetch = {str(cfg.allow_web_fetch).lower()}\n"
        f"allow_web_crawl = {str(cfg.allow_web_crawl).lower()}\n"
        f"allow_explore = {str(cfg.allow_explore).lower()}\n"
        f'active_experience_id = "{cfg.active_experience_id}"\n'
        f"amnesia = {str(cfg.amnesia).lower()}\n\n"
        "[base]\n"
        f'network = "{base.network}"\n'
        f"chain_id = {base.chain_id}\n"
        f'rpc = "{base.rpc}"\n'
        f'approval_mode = "{base.approval_mode}"\n'
        f"mainnet_enabled = {str(base.mainnet_enabled).lower()}\n"
        f"per_action_limit_wei = {base.per_action_limit_wei}\n"
        f"cumulative_limit_wei = {base.cumulative_limit_wei}\n"
        f'wallet_path = "{_toml_path(base.wallet_path)}"\n'
        f"dry_run = {str(base.dry_run).lower()}\n\n"
        + "\n".join(brains)
        + ("\n\n" + "\n".join(mcp_blocks) if mcp_blocks else "")
        + ("\n\n" + "\n".join(channel_blocks) if channel_blocks else "")
        + "\n"
    )
