"""Discover, install, and apply Experience packs."""

from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from anima.config.schema import AnimaConfig, McpServerConfig, save_config
from anima.experiences.schema import ExperienceManifest
from anima.memory.sibyl_adapter import DisabledMemory, SibylAdapter
from anima.memory.writer import remember_strategy, update_self
from anima.skills.catalog import SKILLS, apply_skill_grants

Memory = SibylAdapter | DisabledMemory


@dataclass(frozen=True)
class ExperiencePack:
    manifest: ExperienceManifest
    path: Path
    source: str  # bundled | installed | local

    @property
    def id(self) -> str:
        return self.manifest.id


def repo_experiences_dir() -> Path:
    here = Path(__file__).resolve().parent
    bundled = here / "bundled"
    if bundled.is_dir() and any(bundled.iterdir()):
        return bundled
    root = Path(__file__).resolve().parents[3] / "experiences"
    return root


def installed_experiences_dir(cfg: AnimaConfig) -> Path:
    root = cfg.data_dir / "experiences" / "installed"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_manifest(path: Path) -> ExperienceManifest | None:
    file = path / "experience.toml"
    if not file.is_file():
        return None
    raw = tomllib.loads(file.read_text(encoding="utf-8"))
    return ExperienceManifest.from_toml(raw)


def _scan_dir(root: Path, source: str) -> list[ExperiencePack]:
    if not root.is_dir():
        return []
    packs: list[ExperiencePack] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        manifest = _load_manifest(child)
        if manifest:
            packs.append(ExperiencePack(manifest=manifest, path=child, source=source))
    return packs


def list_experiences(cfg: AnimaConfig) -> list[ExperiencePack]:
    seen: set[str] = set()
    out: list[ExperiencePack] = []
    for source, root in (
        ("installed", installed_experiences_dir(cfg)),
        ("bundled", repo_experiences_dir()),
    ):
        for pack in _scan_dir(root, source):
            if pack.id in seen:
                continue
            seen.add(pack.id)
            out.append(pack)
    return out


def load_experience(cfg: AnimaConfig, exp_id: str) -> ExperiencePack | None:
    for pack in list_experiences(cfg):
        if pack.id == exp_id:
            return pack
    return None


def install_experience(cfg: AnimaConfig, exp_id: str) -> Path:
    pack = load_experience(cfg, exp_id)
    if pack is None:
        raise FileNotFoundError(f"experience {exp_id!r} not found in marketplace")
    if pack.source == "installed":
        return pack.path
    dest = installed_experiences_dir(cfg) / exp_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(pack.path, dest)
    return dest


def apply_experience(cfg: AnimaConfig, memory: Memory, exp_id: str, *, install: bool = True) -> ExperiencePack:
    if install:
        install_experience(cfg, exp_id)
    pack = load_experience(cfg, exp_id)
    if pack is None:
        raise FileNotFoundError(exp_id)

    caps = pack.manifest.capabilities
    fetch = caps.web_fetch if caps.web_fetch is not None else cfg.allow_web_fetch
    crawl = caps.web_crawl if caps.web_crawl is not None else cfg.allow_web_crawl
    explore = caps.explore if caps.explore is not None else cfg.allow_explore
    for skill in pack.manifest.skills:
        if skill.capability == "web_fetch" and skill.grant:
            fetch = True
        if skill.capability == "web_crawl" and skill.grant:
            crawl = True
        if skill.capability == "web_explore" or skill.capability == "explore":
            if skill.grant:
                explore = True
    apply_skill_grants(cfg, fetch=fetch, crawl=crawl, explore=explore)
    if caps.shell is not None:
        cfg.allow_shell = caps.shell

    cfg.mcp_servers = []
    for item in pack.manifest.mcp:
        # Built-in in-process Sibyl bridge — no external `sibyl mcp` subprocess required.
        if item.id in {"sibyl", "anima-sibyl"}:
            continue
        cfg.mcp_servers.append(
            McpServerConfig(
                id=item.id,
                title=item.title or item.id,
                command=item.command,
                args=item.args,
                env=item.env,
                enabled=True,
                optional=item.optional,
            )
        )

    cfg.channels = []
    for ch in pack.manifest.channels:
        from anima.config.schema import ChannelConfig

        cfg.channels.append(ChannelConfig(kind=ch.kind, enabled=ch.enabled, note=ch.note))

    cfg.active_experience_id = pack.id
    save_config(cfg)

    if memory.enabled:
        persona = pack.manifest.personality
        patch: dict = {"experience_id": pack.id, "experience_title": pack.manifest.title}
        if persona.self_description:
            patch["self_description"] = persona.self_description
        if persona.name_hint:
            patch.setdefault("name", persona.name_hint)
        if persona.values:
            patch["values"] = persona.values
        update_self(memory, patch)
        if persona.strategy_hint:
            remember_strategy(memory, f"experience-{pack.id}", persona.strategy_hint, worked=True)

    return pack


def format_marketplace(cfg: AnimaConfig) -> str:
    packs = list_experiences(cfg)
    if not packs:
        return "No experience packs found. Add folders under experiences/ with experience.toml."
    active = cfg.active_experience_id
    lines = ["Experiences Marketplace — skills + MCP + personality + channels", ""]
    for pack in packs:
        mark = "*" if pack.id == active else " "
        tags = ", ".join(pack.manifest.tags[:4]) or "—"
        lines.append(
            f"{mark} {pack.id:<16} {pack.manifest.title:<22} [{pack.source}]  {pack.manifest.summary[:60]}"
        )
        lines.append(f"    tags: {tags}  ·  skills: {len(pack.manifest.skills)}  ·  mcp: {len(pack.manifest.mcp)}")
    lines += ["", "Apply: anima experiences apply <id>  ·  In chat: /experiences apply <id>"]
    return "\n".join(lines)
