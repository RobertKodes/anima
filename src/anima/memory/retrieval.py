"""Retrieve a small, relevant context package from Sibyl before every reply."""

from __future__ import annotations

from typing import Any

from anima.core.context import ContextPackage
from anima.core.events import Intent, TraceItem
from anima.memory.sibyl_adapter import (
    CAT_BRAIN_PERF,
    CAT_CAPABILITY,
    CAT_GOAL,
    CAT_KNOWLEDGE,
    CAT_ONCHAIN,
    CAT_PERSON,
    CAT_POLICY,
    CAT_SELF,
    CAT_STRATEGY,
    SELF_NAME,
    DisabledMemory,
    SibylAdapter,
)

Memory = SibylAdapter | DisabledMemory


def build_context(memory: Memory, intent: Intent, *, amnesia: bool = False) -> tuple[ContextPackage, list[TraceItem]]:
    if amnesia or not memory.enabled:
        return ContextPackage(amnesia=True, query=intent.raw), [
            TraceItem(kind="mode", name="amnesia", why="Sibyl retrieval is disabled for this turn")
        ]

    traces: list[TraceItem] = []
    pkg = ContextPackage(query=intent.raw)
    self_row = memory.get_entity(CAT_SELF, SELF_NAME)
    if self_row:
        pkg.self_model = _body(self_row)
        traces.append(TraceItem("self", SELF_NAME, "loaded durable self-model", _preview(pkg.self_model)))

    pkg.people = [_row(e) for e in memory.list_entities(CAT_PERSON, limit=20)]
    pkg.goals = [_row(e) for e in memory.list_entities(CAT_GOAL, limit=20)]
    pkg.strategies = [_row(e) for e in memory.list_entities(CAT_STRATEGY, limit=20)]
    pkg.policies = [_row(e) for e in memory.list_entities(CAT_POLICY, limit=20)]
    pkg.knowledge = [_row(e) for e in memory.list_entities(CAT_KNOWLEDGE, limit=20)]
    pkg.onchain = [_row(e) for e in memory.list_entities(CAT_ONCHAIN, limit=10)]
    pkg.brain_perf = [_row(e) for e in memory.list_entities(CAT_BRAIN_PERF, limit=10)]
    pkg.capabilities = [_row(e) for e in memory.list_entities(CAT_CAPABILITY, limit=20)]

    hits = memory.search(intent.raw, limit=8) if intent.raw.strip() else []
    episodes = []
    for hit in hits:
        traces.append(
            TraceItem(
                kind=str(hit.get("tier") or hit.get("category") or "search"),
                name=str(hit.get("name") or hit.get("key") or hit.get("id") or "hit"),
                why="FTS5 match for current intent",
                preview=_preview(hit),
            )
        )
        if hit.get("category") == "experience" or hit.get("tier") == "journal":
            episodes.append(_row(hit))
    journal = memory.read_events(limit=8)
    for event in journal:
        episodes.append(
            {
                "name": "journal",
                "body": {
                    "acted": event.get("acted"),
                    "evaluated": event.get("evaluated"),
                    "extra": event.get("extra"),
                    "ts": event.get("ts"),
                },
            }
        )
    pkg.experiences = episodes[:10]

    if pkg.people:
        traces.append(TraceItem("relationship", "people", f"{len(pkg.people)} known relationship(s)"))
    if pkg.goals:
        traces.append(TraceItem("goal", "goals", f"{len(pkg.goals)} stored goal(s)"))
    if pkg.policies:
        traces.append(TraceItem("policy", "policies", f"{len(pkg.policies)} stored policy(ies)"))
    if pkg.strategies:
        traces.append(TraceItem("strategy", "strategies", f"{len(pkg.strategies)} learned strateg(ies)"))
    return pkg, traces


def _body(row: dict[str, Any]) -> dict[str, Any]:
    body = row.get("body")
    return body if isinstance(body, dict) else {"value": body}


def _row(row: dict[str, Any]) -> dict[str, Any]:
    return {"name": row.get("name"), "category": row.get("category"), "body": _body(row), "id": row.get("id")}


def _preview(value: Any) -> str:
    text = str(value)
    return text if len(text) < 160 else text[:157] + "..."
