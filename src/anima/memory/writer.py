"""Persist experiences, relationships, goals, and outcomes into Sibyl after every turn."""

from __future__ import annotations

from typing import Any

from anima.core.events import utcnow
from anima.memory.sibyl_adapter import (
    CAT_BRAIN_PERF,
    CAT_CAPABILITY,
    CAT_EXPERIENCE,
    CAT_GOAL,
    CAT_KNOWLEDGE,
    CAT_ONCHAIN,
    CAT_PERSON,
    CAT_POLICY,
    CAT_SELF,
    CAT_STRATEGY,
    SELF_NAME,
    slug,
    DisabledMemory,
    SibylAdapter,
)

Memory = SibylAdapter | DisabledMemory

SECRET_MARKERS = ("private_key", "privkey", "seed phrase", "mnemonic", "0x" + "0" * 40)


def ensure_newborn(memory: Memory) -> dict[str, Any]:
    existing = memory.get_entity(CAT_SELF, SELF_NAME)
    if existing:
        return existing
    body = {
        "born": True,
        "name": None,
        "self_description": "I just woke up. I have no life before this.",
        "values": [],
        "known_abilities": ["conversation", "memory"],
        "limitations": ["no fabricated history", "no unrestricted spending"],
        "stage_hint": "newborn",
        "created_at": utcnow(),
    }
    row = memory.set_entity(CAT_SELF, SELF_NAME, body, status="active")
    memory.write_event(
        evaluated={"kind": "birth"},
        acted=["initialized first experience"],
        extra={"domain": "self"},
    )
    memory.set_state("session", {"born_at": utcnow(), "turns": 0})
    return row


def remember_person(memory: Memory, name: str, note: str = "") -> dict[str, Any]:
    key = slug(name, fallback="person")
    existing = memory.get_entity(CAT_PERSON, key)
    body = {
        "name": name.strip(),
        "summary": note or f"Known as {name.strip()}.",
        "first_met": utcnow(),
        "interactions": 1,
        "commitments": [],
        "trust_evidence": [],
    }
    if existing and isinstance(existing.get("body"), dict):
        prev = existing["body"]
        body["first_met"] = prev.get("first_met") or body["first_met"]
        body["interactions"] = int(prev.get("interactions") or 0) + 1
        if note:
            body["summary"] = note
        elif prev.get("summary"):
            body["summary"] = prev["summary"]
        body["commitments"] = list(prev.get("commitments") or [])
        body["trust_evidence"] = list(prev.get("trust_evidence") or [])
    row = memory.set_entity(CAT_PERSON, key, body, status="active")
    memory.write_event(acted=[f"relationship with {name.strip()}"], extra={"domain": "relationship", "name": name})
    return row


def remember_goal(memory: Memory, title: str, detail: str = "", origin: str = "user") -> dict[str, Any]:
    key = slug(title, fallback="goal")
    body = {
        "title": title.strip(),
        "summary": detail or title.strip(),
        "origin": origin,
        "priority": "normal",
        "status": "active",
        "dependencies": [],
        "evidence": [],
        "updated_at": utcnow(),
    }
    row = memory.set_entity(CAT_GOAL, key, body, status="active")
    memory.write_event(acted=[f"goal recorded: {title.strip()}"], extra={"domain": "goal"})
    return row


def remember_policy(memory: Memory, name: str, policy: dict[str, Any]) -> dict[str, Any]:
    body = {"name": name, "policy": policy, "updated_at": utcnow()}
    row = memory.set_entity(CAT_POLICY, slug(name, fallback="policy"), body, status="active")
    memory.write_event(acted=[f"policy recorded: {name}"], extra={"domain": "policy"})
    return row


def remember_strategy(memory: Memory, name: str, summary: str, worked: bool, conditions: str = "") -> dict[str, Any]:
    body = {
        "name": name,
        "summary": summary,
        "worked": worked,
        "conditions": conditions,
        "updated_at": utcnow(),
    }
    row = memory.set_entity(CAT_STRATEGY, slug(name, fallback="strategy"), body, status="active")
    memory.write_event(acted=[f"strategy recorded: {name}"], extra={"domain": "strategy", "worked": worked})
    return row


def remember_knowledge(memory: Memory, name: str, text: str) -> dict[str, Any]:
    body = {"name": name, "summary": text, "updated_at": utcnow()}
    return memory.set_entity(CAT_KNOWLEDGE, slug(name, fallback="knowledge"), body, status="active")


def record_experience(
    memory: Memory,
    user_text: str,
    reply_text: str,
    intent: str,
    brain_id: str,
    extra: dict[str, Any] | None = None,
) -> str:
    payload = extra or {}
    _assert_no_secrets(user_text)
    _assert_no_secrets(reply_text)
    _assert_no_secrets(str(payload))
    event_id = memory.write_event(
        evaluated={"intent": intent, "user": user_text[:2000]},
        acted={"reply": reply_text[:2000], "brain": brain_id},
        extra={k: v for k, v in payload.items() if k not in ("private_key", "seed", "mnemonic")},
    )
    memory.set_entity(
        CAT_EXPERIENCE,
        slug(event_id[:12], fallback="exp"),
        {
            "intent": intent,
            "user": user_text[:500],
            "reply": reply_text[:500],
            "brain": brain_id,
            "ts": utcnow(),
        },
        status="active",
    )
    session = memory.get_state("session") or {"turns": 0}
    session["turns"] = int(session.get("turns") or 0) + 1
    session["last_turn"] = utcnow()
    memory.set_state("session", session)
    return event_id


def record_brain_outcome(memory: Memory, brain_id: str, task: str, ok: bool, latency_ms: int, note: str = "") -> None:
    existing = memory.get_entity(CAT_BRAIN_PERF, slug(brain_id, fallback="brain"))
    body = {"brain_id": brain_id, "successes": 0, "failures": 0, "last_task": task, "last_ok": ok, "latency_ms": latency_ms, "note": note}
    if existing and isinstance(existing.get("body"), dict):
        prev = existing["body"]
        body["successes"] = int(prev.get("successes") or 0)
        body["failures"] = int(prev.get("failures") or 0)
    if ok:
        body["successes"] += 1
    else:
        body["failures"] += 1
    memory.set_entity(CAT_BRAIN_PERF, slug(brain_id, fallback="brain"), body, status="active")


def record_capability(memory: Memory, name: str, action: str, detail: str = "") -> None:
    memory.set_entity(
        CAT_CAPABILITY,
        slug(f"{name}-{action}", fallback="cap"),
        {"name": name, "action": action, "detail": detail, "ts": utcnow()},
        status="active",
    )
    memory.write_event(acted=[f"capability {action}: {name}"], extra={"domain": "capability"})


def record_onchain(memory: Memory, record: dict[str, Any]) -> dict[str, Any]:
    safe = {k: v for k, v in record.items() if k not in ("private_key", "seed", "mnemonic", "signing_key")}
    _assert_no_secrets(str(safe))
    name = slug(str(safe.get("tx_id") or safe.get("intent") or "tx"), fallback="tx")
    row = memory.set_entity(CAT_ONCHAIN, name, safe, status=str(safe.get("status") or "recorded"))
    memory.write_event(acted=["base action recorded"], extra={"domain": "onchain", "tx_id": safe.get("tx_id")})
    return row


def save_last_trace(memory: Memory, trace: dict[str, Any]) -> None:
    memory.set_state("last_decision", trace)


def load_last_trace(memory: Memory) -> dict[str, Any] | None:
    return memory.get_state("last_decision")


def update_self(memory: Memory, patch: dict[str, Any]) -> dict[str, Any]:
    current = memory.get_entity(CAT_SELF, SELF_NAME)
    body = dict(current.get("body") or {}) if current else {}
    body.update(patch)
    body["updated_at"] = utcnow()
    return memory.set_entity(CAT_SELF, SELF_NAME, body, status="active")


def _assert_no_secrets(text: str) -> None:
    lowered = text.lower()
    if "seed phrase" in lowered or "mnemonic" in lowered:
        raise ValueError("refusing to persist a seed phrase or mnemonic")
    if "private_key" in lowered and "0x" in lowered and len(text) > 60:
        raise ValueError("refusing to persist a signing secret")
