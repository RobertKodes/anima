"""Tests for Sibyl Memory credentials, factory, and in-process MCP bridge."""

from __future__ import annotations

import json

from anima.config.schema import default_config
from anima.core.runtime import Runtime
from anima.memory.factory import open_memory
from anima.memory.sibyl_adapter import DisabledMemory, SibylAdapter
from anima.memory.sibyl_credentials import credential_paths, resolve_sibyl_auth
from anima.mcp.sibyl_bridge import BUILTIN_SERVER_ID


def test_resolve_sibyl_auth_from_secrets(data_dir, monkeypatch) -> None:
    cfg = default_config(data_dir)
    secrets = cfg.data_dir / "secrets" / "sibyl.json"
    secrets.parent.mkdir(parents=True, exist_ok=True)
    secrets.write_text(
        json.dumps({"account_id": "acc-test", "session_token": "tok", "tier": "pro"}),
        encoding="utf-8",
    )
    monkeypatch.delenv("SIBYL_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("SIBYL_SESSION_TOKEN", raising=False)
    auth = resolve_sibyl_auth(cfg)
    assert auth["account_id"] == "acc-test"
    assert auth["session_token"] == "tok"
    assert auth["tier"] == "pro"


def test_open_memory_amnesia(data_dir) -> None:
    cfg = default_config(data_dir)
    cfg.amnesia = True
    mem = open_memory(cfg)
    assert isinstance(mem, DisabledMemory)
    assert mem.enabled is False


def test_open_memory_local_sibyl(data_dir) -> None:
    cfg = default_config(data_dir)
    mem = open_memory(cfg)
    assert isinstance(mem, SibylAdapter)
    health = mem.health()
    assert health.get("ok") is True
    mem.close()


def test_builtin_sibyl_mcp_bridge(data_dir) -> None:
    cfg = default_config(data_dir)
    runtime = Runtime(cfg)
    runtime.boot()
    status = runtime.mcp.format_status()
    assert BUILTIN_SERVER_ID in status
    tools = runtime.mcp.discover_tools(BUILTIN_SERVER_ID)
    names = {t.name for t in tools}
    assert {"search", "recent", "self", "people"}.issubset(names)
    runtime.memory.set_entity("person", "alice", {"name": "Alice", "summary": "friend"})
    out = runtime.mcp.call(BUILTIN_SERVER_ID, "search", {"query": "Alice"})
    assert "Alice" in out


def test_sibyl_status_command(data_dir) -> None:
    from anima.app.commands import cmd_sibyl

    cfg = default_config(data_dir)
    runtime = Runtime(cfg)
    reply = cmd_sibyl(runtime, ["status"])
    assert "Sibyl Memory" in reply.text


def test_credential_paths_include_anima_secrets(data_dir) -> None:
    cfg = default_config(data_dir)
    paths = credential_paths(cfg)
    assert cfg.data_dir / "secrets" / "sibyl.json" in paths
