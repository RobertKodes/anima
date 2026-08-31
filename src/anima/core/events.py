"""In-process events. Durable history is written to Sibyl, not kept here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


IntentKind = Literal[
    "chat",
    "remember_person",
    "set_goal",
    "set_policy",
    "ask_identity",
    "ask_memory",
    "code",
    "base_action",
    "web_fetch",
    "web_crawl",
    "explore",
    "sleep",
    "status",
    "unknown",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class Intent:
    kind: IntentKind
    raw: str
    slots: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceItem:
    kind: str
    name: str
    why: str
    preview: str = ""


@dataclass
class DecisionTrace:
    """Inspectable cause of the last reply. Never stores chain-of-thought or secrets."""

    intent: IntentKind
    brain_id: str
    memories: list[TraceItem] = field(default_factory=list)
    tools: list[TraceItem] = field(default_factory=list)
    policy: str = ""
    amnesia: bool = False
    created_at: str = field(default_factory=utcnow)

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "brain_id": self.brain_id,
            "memories": [item.__dict__ for item in self.memories],
            "tools": [item.__dict__ for item in self.tools],
            "policy": self.policy,
            "amnesia": self.amnesia,
            "created_at": self.created_at,
        }


@dataclass
class Reply:
    text: str
    birth: bool = False
    traces: DecisionTrace | None = None
    notices: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamPart:
    """Incremental event while the being composes a reply."""

    kind: Literal["status", "think", "token", "done"]
    text: str = ""
    reply: Reply | None = None
