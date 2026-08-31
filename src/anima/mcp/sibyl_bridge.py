"""In-process Sibyl Memory tools — no subprocess; same store as Runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from anima.memory.sibyl_adapter import CAT_PERSON, CAT_SELF, DisabledMemory, SELF_NAME, SibylAdapter

Memory = SibylAdapter | DisabledMemory

BUILTIN_SERVER_ID = "anima-sibyl"


@dataclass(frozen=True)
class SibylTool:
    name: str
    description: str


TOOLS: tuple[SibylTool, ...] = (
    SibylTool("search", "FTS5 search across all Sibyl tiers (entities, journal, state)."),
    SibylTool("recent", "Recent journal events from Sibyl."),
    SibylTool("self", "Load the durable self-model entity from Sibyl."),
    SibylTool("people", "List known relationships stored in Sibyl."),
)


class SibylBridge:
    """Expose Sibyl MemoryClient operations as MCP-style tools for the brain."""

    def __init__(self, memory: Memory) -> None:
        self.memory = memory

    @property
    def available(self) -> bool:
        return isinstance(self.memory, SibylAdapter) and self.memory.enabled

    def list_tools(self) -> list[SibylTool]:
        return list(TOOLS) if self.available else []

    def call(self, tool_name: str, arguments: dict[str, Any] | None = None) -> str:
        if not self.available:
            return "Sibyl memory is disabled (amnesia mode)."
        args = arguments or {}
        if tool_name == "search":
            query = str(args.get("query") or args.get("q") or "").strip()
            if not query:
                return "Usage: query=..."
            hits = self.memory.search(query, limit=int(args.get("limit") or 8))
            if not hits:
                return f"No Sibyl hits for {query!r}."
            lines = [f"Sibyl search: {query!r}"]
            for hit in hits:
                lines.append(
                    f"- [{hit.get('tier') or hit.get('category')}] "
                    f"{hit.get('name') or hit.get('key') or hit.get('id')}"
                )
            return "\n".join(lines)
        if tool_name == "recent":
            limit = int(args.get("limit") or 10)
            events = self.memory.read_events(limit=limit)
            if not events:
                return "No journal events in Sibyl yet."
            lines = ["Recent Sibyl journal:"]
            for event in events:
                lines.append(f"- {event.get('ts')}: {event.get('acted')}")
            return "\n".join(lines)
        if tool_name == "self":
            row = self.memory.get_entity(CAT_SELF, SELF_NAME)
            if not row:
                return "No self entity in Sibyl — this being is newborn."
            return f"Sibyl self/being: {row.get('body') or row}"
        if tool_name == "people":
            rows = self.memory.list_entities(CAT_PERSON, limit=int(args.get("limit") or 20))
            if not rows:
                return "No people entities in Sibyl yet."
            lines = ["Sibyl people:"]
            for row in rows:
                body = row.get("body") or {}
                name = body.get("name") or row.get("name")
                lines.append(f"- {name}: {body.get('summary') or ''}")
            return "\n".join(lines)
        return f"Unknown Sibyl tool {tool_name!r}. Try: search, recent, self, people"
