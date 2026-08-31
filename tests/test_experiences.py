"""Tests for Experiences Marketplace."""

from __future__ import annotations

from anima.config.schema import default_config
from anima.core.runtime import Runtime
from anima.experiences.marketplace import apply_experience, list_experiences, load_experience


def test_marketplace_lists_bundled_packs(data_dir) -> None:
    cfg = default_config(data_dir)
    packs = list_experiences(cfg)
    ids = {p.id for p in packs}
    assert "scholar" in ids
    assert "guardian" in ids
    assert "messenger" in ids


def test_apply_scholar_grants_web_and_personality(data_dir) -> None:
    cfg = default_config(data_dir)
    runtime = Runtime(cfg)
    runtime.boot()
    pack = apply_experience(cfg, runtime.memory, "scholar")
    assert pack.id == "scholar"
    assert cfg.allow_web_fetch is True
    assert cfg.allow_explore is True
    assert cfg.active_experience_id == "scholar"
    row = runtime.memory.get_entity("self", "being")
    body = (row or {}).get("body") or {}
    assert "scholar" in str(body.get("self_description", "")).lower()


def test_experiences_command_list(data_dir) -> None:
    from anima.app.commands import cmd_experiences

    cfg = default_config(data_dir)
    runtime = Runtime(cfg)
    reply = cmd_experiences(runtime, ["list"])
    assert "scholar" in reply.text
    assert "Marketplace" in reply.text


def test_mcp_registry_has_builtin_sibyl(data_dir) -> None:
    cfg = default_config(data_dir)
    runtime = Runtime(cfg)
    assert "anima-sibyl" in runtime.mcp.format_status()
    tools = runtime.mcp.discover_tools("anima-sibyl")
    assert len(tools) >= 4


def test_load_unknown_experience(data_dir) -> None:
    cfg = default_config(data_dir)
    assert load_experience(cfg, "does-not-exist") is None
