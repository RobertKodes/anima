"""Load Sibyl Memory credentials for Pro tier and server-verified caps."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from anima.config.schema import AnimaConfig


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    out["account_id"] = raw.get("account_id") or raw.get("accountId")
    out["session_token"] = (
        raw.get("session_token") or raw.get("bearer_token") or raw.get("access_token") or raw.get("token")
    )
    out["tier"] = raw.get("tier") or raw.get("plugin_tier")
    if raw.get("credentials_claim"):
        out["credentials_claim"] = raw["credentials_claim"]
    if raw.get("credentials_signature"):
        out["credentials_signature"] = raw["credentials_signature"]
    return {k: v for k, v in out.items() if v}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def credential_paths(cfg: AnimaConfig) -> list[Path]:
    return [
        cfg.data_dir / "secrets" / "sibyl.json",
        Path.home() / ".sibyl-memory" / "credentials.json",
    ]


def resolve_sibyl_auth(cfg: AnimaConfig) -> dict[str, Any]:
    """Merge Sibyl auth from Anima secrets, Sibyl CLI credentials, and env."""
    merged: dict[str, Any] = {}

    for path in credential_paths(cfg):
        data = _read_json(path)
        if data:
            merged.update(_normalize(data))

    if os.environ.get("SIBYL_ACCOUNT_ID"):
        merged["account_id"] = os.environ["SIBYL_ACCOUNT_ID"]
    if os.environ.get("SIBYL_SESSION_TOKEN"):
        merged["session_token"] = os.environ["SIBYL_SESSION_TOKEN"]
    if os.environ.get("SIBYL_TIER"):
        merged["tier"] = os.environ["SIBYL_TIER"]

    if cfg.sibyl_tier:
        merged["tier"] = cfg.sibyl_tier

    return merged


def sibyl_cli_on_path() -> str | None:
    import shutil

    for name in ("sibyl", "sibyl.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def format_sibyl_status(cfg: AnimaConfig, health: dict[str, Any]) -> str:
    auth = resolve_sibyl_auth(cfg)
    lines = [
        "Sibyl Memory (identity store — not markdown, not prompt)",
        f"  db .............. {health.get('path') or cfg.sibyl_db}",
        f"  tenant .......... {health.get('tenant_id') or cfg.tenant_id}",
        f"  tier ............ {health.get('tier') or auth.get('tier') or 'free'}",
        f"  bytes ........... {health.get('bytes', 0)}",
    ]
    if auth.get("account_id"):
        lines.append(f"  account ......... {str(auth['account_id'])[:8]}… (Pro auth loaded)")
    else:
        lines.append("  account ......... (none — run: sibyl init  or  anima sibyl setup)")
    free = health.get("free_tier") or {}
    if isinstance(free, dict) and free.get("cap_bytes"):
        used = free.get("used_bytes") or health.get("bytes") or 0
        cap = free["cap_bytes"]
        pct = int(100 * used / cap) if cap else 0
        lines.append(f"  cap ............. {used}/{cap} bytes ({pct}%)")
    cli = sibyl_cli_on_path()
    lines.append(f"  sibyl CLI ....... {cli or 'not on PATH (pip install sibyl-memory-cli[mcp])'}")
    lines.append("")
    lines.append("Every turn: retrieval.py → context package → brain → writer.py → Sibyl")
    lines.append("Commands: /memory recent | /memory search | /sibyl status | /sibyl lint")
    return "\n".join(lines)
