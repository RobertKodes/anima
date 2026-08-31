"""Small context packages assembled from Sibyl. The model never sees the whole store."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextPackage:
    amnesia: bool = False
    self_model: dict[str, Any] | None = None
    people: list[dict[str, Any]] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)
    strategies: list[dict[str, Any]] = field(default_factory=list)
    knowledge: list[dict[str, Any]] = field(default_factory=list)
    experiences: list[dict[str, Any]] = field(default_factory=list)
    policies: list[dict[str, Any]] = field(default_factory=list)
    onchain: list[dict[str, Any]] = field(default_factory=list)
    brain_perf: list[dict[str, Any]] = field(default_factory=list)
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    query: str = ""

    def is_newborn(self) -> bool:
        if self.amnesia:
            return True
        # Birth writes a journal row. That is not a life yet.
        return not bool(self.people or self.goals or self.policies)

    def as_prompt(self) -> str:
        if self.amnesia:
            return "CONTEXT PACKAGE: empty (amnesia mode). You have no durable memories."
        if self.is_newborn() and not self.self_model:
            return "CONTEXT PACKAGE: empty. This is the first experience. No name, no history."
        parts = ["CONTEXT PACKAGE (authoritative; do not invent beyond it):"]
        if self.self_model:
            parts.append(f"SELF: {self.self_model}")
        if self.people:
            parts.append("PEOPLE: " + "; ".join(_brief(p) for p in self.people[:6]))
        if self.goals:
            parts.append("GOALS: " + "; ".join(_brief(g) for g in self.goals[:6]))
        if self.strategies:
            parts.append("STRATEGIES: " + "; ".join(_brief(s) for s in self.strategies[:6]))
        if self.policies:
            parts.append("POLICIES: " + "; ".join(_brief(p) for p in self.policies[:6]))
        if self.knowledge:
            parts.append("KNOWLEDGE: " + "; ".join(_brief(k) for k in self.knowledge[:6]))
        if self.onchain:
            parts.append("ONCHAIN: " + "; ".join(_brief(o) for o in self.onchain[:4]))
        if self.experiences:
            parts.append("RECENT EXPERIENCE: " + "; ".join(_brief(e) for e in self.experiences[:6]))
        parts.append(
            "Answer the user's actual question using only the context above. "
            "Do not repeat boilerplate about waking up unless they ask who you are."
        )
        return "\n".join(parts)


def _brief(row: dict[str, Any]) -> str:
    body = row.get("body") if isinstance(row.get("body"), dict) else row
    name = row.get("name") or (body or {}).get("name") or (body or {}).get("title") or ""
    summary = ""
    if isinstance(body, dict):
        summary = str(body.get("summary") or body.get("text") or body.get("policy") or "")[:180]
    return f"{name}: {summary}".strip(": ")
