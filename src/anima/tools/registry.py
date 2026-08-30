"""Capability registry. Tools are granted, not faked with XP."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Capability:
    id: str
    title: str
    granted: bool
    summary: str
    risk: str = "low"
    needs_permission: bool = False


@dataclass
class CapabilityRegistry:
    items: list[Capability] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.items:
            self.items = [
                Capability("conversation", "Conversation", True, "Talk with the being."),
                Capability("memory", "Sibyl memory", True, "Read and write durable personal state."),
                Capability("sleep", "Sleep / consolidation", True, "Turn raw history into durable state."),
                Capability("brains", "Multi-brain routing", True, "Register and swap cognitive models."),
                Capability("base", "Base actions", True, "Prepare and execute approved onchain actions.", risk="high", needs_permission=True),
                Capability("shell", "Shell", False, "Run local commands. Off until granted.", risk="high", needs_permission=True),
            ]

    def grant(self, cap_id: str) -> Capability:
        for item in self.items:
            if item.id == cap_id:
                item.granted = True
                return item
        raise KeyError(cap_id)

    def revoke(self, cap_id: str) -> Capability:
        for item in self.items:
            if item.id == cap_id:
                item.granted = False
                return item
        raise KeyError(cap_id)

    def as_dicts(self) -> list[dict]:
        return [item.__dict__.copy() for item in self.items]
