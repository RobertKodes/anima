"""Sleep: turn raw history into durable, inspectable state.

A judge can watch a behavior, run /sleep, restart, and see a changed decision
caused by consolidated memory — not by leftover LLM context.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from anima.core.events import utcnow
from anima.memory.sibyl_adapter import CAT_GOAL, CAT_PERSON, CAT_SELF, SELF_NAME, DisabledMemory, SibylAdapter
from anima.memory.writer import remember_knowledge, remember_strategy, update_self

Memory = SibylAdapter | DisabledMemory

STOP = {
    "the", "a", "an", "and", "or", "to", "of", "i", "you", "we", "it", "is", "are",
    "in", "on", "for", "with", "that", "this", "be", "as", "at", "my", "me", "was",
}


def sleep(memory: Memory, brain_complete=None) -> dict[str, Any]:
    if not memory.enabled:
        return {
            "ok": False,
            "reason": "cannot consolidate without Sibyl",
            "report": "Amnesia mode: there is nothing durable to dream about.",
        }

    events = memory.read_events(limit=80)
    people = memory.list_entities(CAT_PERSON, limit=50)
    goals = memory.list_entities(CAT_GOAL, limit=50)
    self_row = memory.get_entity(CAT_SELF, SELF_NAME)
    self_body = dict((self_row or {}).get("body") or {})

    tokens: list[str] = []
    unresolved: list[str] = []
    for event in events:
        blob = " ".join(_bits(event.get("acted")) + _bits(event.get("evaluated")) + _bits(event.get("extra")))
        for word in blob.lower().replace("/", " ").replace(":", " ").split():
            clean = "".join(ch for ch in word if ch.isalnum())
            if len(clean) > 3 and clean not in STOP:
                tokens.append(clean)
        extra = event.get("extra") or {}
        if isinstance(extra, dict) and extra.get("unresolved"):
            unresolved.append(str(extra["unresolved"]))

    common = [word for word, _n in Counter(tokens).most_common(8)]
    if common:
        remember_knowledge(
            memory,
            "recurring-themes",
            "Repeated themes from recent life: " + ", ".join(common) + ".",
        )

    for person in people:
        body = dict(person.get("body") or {})
        name = body.get("name") or person.get("name")
        if not name:
            continue
        summary = (
            f"{name} is someone I remember. "
            f"We have met {body.get('interactions', 1)} time(s). "
            f"{body.get('summary') or ''}"
        ).strip()
        body["summary"] = summary
        memory.set_entity("person", person["name"], body, status="active")

    active_goals = [g for g in goals if (g.get("body") or {}).get("status") != "done"]
    if active_goals:
        titles = [((g.get("body") or {}).get("title") or g.get("name")) for g in active_goals]
        remember_strategy(
            memory,
            "honor-active-goals",
            "When a new request arrives, check it against active goals: " + ", ".join(str(t) for t in titles) + ".",
            worked=True,
            conditions="any later session",
        )

    description = self_body.get("self_description") or "I am still becoming someone."
    if people:
        names = [((p.get("body") or {}).get("name") or p.get("name")) for p in people]
        description = f"I remember {', '.join(str(n) for n in names)}. {description}"
    if active_goals:
        description += " I am working toward stored goals."
    update_self(
        memory,
        {
            "self_description": description[:500],
            "last_sleep": utcnow(),
            "sleep_cycles": int(self_body.get("sleep_cycles") or 0) + 1,
        },
    )

    report_lines = [
        f"Dream report · {utcnow()}",
        f"Experiences considered: {len(events)}",
        f"Relationships refreshed: {len(people)}",
        f"Active goals: {len(active_goals)}",
        f"Recurring themes: {', '.join(common) or 'none yet'}",
        f"Unresolved: {'; '.join(unresolved) or 'none'}",
        "Self-model and strategies were rewritten into Sibyl.",
        "A fresh session with empty model context should still know this.",
    ]
    if brain_complete:
        try:
            distilled = brain_complete(
                "Summarize what this being should remember after sleep. "
                "Be factual. Do not invent. Use only the dream notes:\n" + "\n".join(report_lines)
            )
            if distilled:
                report_lines.append("Brain distillation: " + distilled.strip()[:800])
                remember_knowledge(memory, "sleep-distillation", distilled.strip()[:800])
        except Exception:
            report_lines.append("Brain distillation skipped (brain unavailable).")

    report = "\n".join(report_lines)
    memory.set_reference("last_dream", {"report": report, "at": utcnow()})
    memory.write_event(acted=["sleep consolidation"], extra={"domain": "sleep", "report": report[:1000]})
    memory.set_state("last_sleep", {"at": utcnow(), "events": len(events)})
    return {"ok": True, "report": report, "themes": common, "people": len(people), "goals": len(active_goals)}


def _bits(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, dict):
        return [str(v) for v in value.values() if not isinstance(v, (dict, list))] + [str(value)]
    return [str(value)]
