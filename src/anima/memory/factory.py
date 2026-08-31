"""Open the Sibyl-backed memory store for a Runtime."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.memory.sibyl_adapter import DisabledMemory, SibylAdapter
from anima.memory.sibyl_credentials import resolve_sibyl_auth

Memory = SibylAdapter | DisabledMemory


def open_memory(cfg: AnimaConfig, *, amnesia: bool = False) -> Memory:
    if amnesia or cfg.amnesia:
        return DisabledMemory()
    auth = resolve_sibyl_auth(cfg)
    tier = auth.get("tier") or cfg.sibyl_tier or "free"
    return SibylAdapter(
        cfg.sibyl_db,
        cfg.tenant_id,
        tier=str(tier),
        account_id=auth.get("account_id"),
        session_token=auth.get("session_token"),
        credentials_claim=auth.get("credentials_claim"),
        credentials_signature=auth.get("credentials_signature"),
    )
