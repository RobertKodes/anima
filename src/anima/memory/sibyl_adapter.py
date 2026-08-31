"""Direct Sibyl MemoryClient adapter.

Every durable personal fact goes through this module. There is no MEMORY.md,
PERSONALITY.md, or USER.md. If this store is removed, the being is gone.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient
from sibyl_memory_client.exceptions import NotFoundError, SibylMemoryError

# Entity categories = memory domains from the PRD, mapped onto Sibyl's WARM tier.
CAT_SELF = "self"
CAT_PERSON = "person"
CAT_GOAL = "goal"
CAT_STRATEGY = "strategy"
CAT_KNOWLEDGE = "knowledge"
CAT_POLICY = "policy"
CAT_BRAIN_PERF = "brain_perf"
CAT_CAPABILITY = "capability"
CAT_ONCHAIN = "onchain"
CAT_EXPERIENCE = "experience"

SELF_NAME = "being"


def slug(value: str, fallback: str = "unnamed") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return (cleaned[:200] or fallback).lower()


class DisabledMemory:
    """Amnesia / deletion-test stand-in. Same shape as SibylAdapter, no store."""

    enabled = False
    path = None

    def health(self) -> dict[str, Any]:
        return {"ok": False, "enabled": False, "reason": "sibyl retrieval disabled"}

    def get_entity(self, category: str, name: str) -> dict[str, Any] | None:
        return None

    def list_entities(self, category: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return []

    def set_entity(self, category: str, name: str, body: dict[str, Any], status: str | None = None) -> dict[str, Any]:
        return {"category": category, "name": name, "body": body, "discarded": True}

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return []

    def write_event(self, **payload: Any) -> str:
        return "discarded"

    def read_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return []

    def set_state(self, key: str, body: dict[str, Any]) -> None:
        return None

    def get_state(self, key: str) -> dict[str, Any] | None:
        return None

    def set_reference(self, key: str, body: Any) -> None:
        return None

    def get_reference(self, key: str) -> dict[str, Any] | None:
        return None


class SibylAdapter:
    """Thin, honest wrapper around MemoryClient.local().

    Judges: this is the write/read critical path.
      write identity  -> set_entity('self', 'being', ...)
      write person    -> set_entity('person', slug, ...)
      write goal      -> set_entity('goal', slug, ...)
      write episode   -> write_event(acted=..., extra=...)
      search          -> search(query)  (FTS5, all tiers)
    """

    enabled = True

    def __init__(self, db_path: Path, tenant_id: str) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tenant_id = tenant_id
        self.client = MemoryClient.local(self.path, tenant_id=tenant_id, tier="free")

    def health(self) -> dict[str, Any]:
        try:
            status = self.client.free_tier_status()
        except SibylMemoryError as exc:
            return {"ok": False, "enabled": True, "path": str(self.path), "error": str(exc)}
        exists = self.path.exists()
        size = self.path.stat().st_size if exists else 0
        return {
            "ok": True,
            "enabled": True,
            "path": str(self.path),
            "tenant_id": self.client.get_tenant(),
            "bytes": size,
            "tier": self.client.get_tier(),
            "free_tier": status,
        }

    def get_entity(self, category: str, name: str) -> dict[str, Any] | None:
        try:
            return self.client.get_entity(category, slug(name, fallback=category))
        except NotFoundError:
            return None

    def list_entities(self, category: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.client.list_entities(category, limit=limit)

    def set_entity(self, category: str, name: str, body: dict[str, Any], status: str | None = None) -> dict[str, Any]:
        return self.client.set_entity(category, slug(name, fallback=category), body, status=status)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        return self.client.search(query, limit=limit)

    def write_event(self, **payload: Any) -> str:
        return self.client.write_event(
            evaluated=payload.get("evaluated"),
            acted=payload.get("acted"),
            forward=payload.get("forward"),
            extra=payload.get("extra"),
        )

    def read_events(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.client.read_events(limit=limit)
        cleaned = []
        for row in rows:
            item = dict(row)
            for key in ("evaluated", "acted", "forward", "extra"):
                if item.get(key) is None:
                    item[key] = None
            cleaned.append(item)
        return cleaned

    def set_state(self, key: str, body: dict[str, Any]) -> None:
        self.client.set_state(key, body)

    def get_state(self, key: str) -> dict[str, Any] | None:
        row = self.client.get_state(key)
        if row is None:
            return None
        body = row.get("body") if isinstance(row, dict) else row
        return body if isinstance(body, dict) else {"value": body, "updated_at": (row or {}).get("updated_at")}

    def set_reference(self, key: str, body: Any) -> None:
        self.client.set_reference(key, body)

    def get_reference(self, key: str) -> dict[str, Any] | None:
        return self.client.get_reference(key)

    def close(self) -> None:
        storage = getattr(self.client, "_storage", None)
        if storage is not None:
            closer = getattr(storage, "close", None)
            if callable(closer):
                closer()
        self.client = None  # type: ignore[assignment]

    def __enter__(self) -> SibylAdapter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
