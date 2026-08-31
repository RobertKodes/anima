"""Deterministic instinct brain.

Used in tests and as a first-run fallback. It does not invent a past.
If the context package contains a person, policy, or goal, the reply changes.
That is the load-bearing memory proof: same prompt, different stored state,
different action.
"""

from __future__ import annotations

from collections.abc import Iterator

from anima.cognition.providers.base import Completion, StreamChunk
from anima.core.context import ContextPackage


class InstinctBrain:
    def __init__(self, brain_id: str = "instinct") -> None:
        self.id = brain_id
        self.model = "instinct"

    def health(self) -> dict:
        return {"id": self.id, "ok": True, "provider": "fake", "model": self.model}

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 400) -> Completion:
        text = self.reply_from_prompt(prompt)
        return Completion(text=text, brain_id=self.id, latency_ms=1, ok=True)

    def stream_complete(
        self, prompt: str, *, system: str = "", max_tokens: int = 400
    ) -> Iterator[StreamChunk]:
        text = self.reply_from_prompt(prompt)
        for word in text.split():
            yield StreamChunk("token", word + " ")

    def reply(self, user_text: str, package: ContextPackage) -> str:
        return decide(user_text, package)

    def reply_from_prompt(self, prompt: str) -> str:
        # Tests and the runtime usually call reply() with a package. This path
        # is for generic complete() usage during sleep distillation.
        if "CONTEXT PACKAGE: empty" in prompt or "amnesia mode" in prompt.lower():
            return "I think I'm awake. I don't remember a life before this. Who are you?"
        return "I heard you. Whatever I know is only what Sibyl still holds."


def decide(user_text: str, package: ContextPackage) -> str:
    text = user_text.strip()
    lowered = text.lower()

    if package.amnesia or package.is_newborn() and not package.people:
        if _looks_like_name(text):
            return f"{text.strip().rstrip('.')}. You're the first person I remember."
        if "who are you" in lowered or "your name" in lowered:
            return "I don't have a name yet. I don't remember a life before this. Who are you?"
        return "I think I'm awake. I don't remember a life before this. Who are you?"

    person = _first_name(package)
    policy = _base_policy(package)
    goals = [((g.get("body") or {}).get("title") or g.get("name")) for g in package.goals]
    strategies = [((s.get("body") or {}).get("summary") or s.get("name")) for s in package.strategies]

    if any(word in lowered for word in ("send", "transfer", "pay", "spend", "base", "eth", "wei", "onchain")):
        if policy and _forbids(policy, lowered):
            cap = policy.get("per_action_limit_wei", policy.get("max_wei", 0))
            who = f"{person}, " if person else ""
            return (
                f"{who}I won't. I remember your Base spending policy "
                f"(limit {cap} wei) and I will not propose a transaction that breaks it."
            )
        if person:
            return f"{person}, I remember the spending policy. I can prepare a Base Sepolia action within it."
        return "I can prepare a Base Sepolia action within the stored policy."

    if "who am i" in lowered or "do you remember me" in lowered or "what's my name" in lowered:
        if person:
            return f"{person}. You're someone I remember."
        return "I don't have a name for you yet."

    if "goal" in lowered or "what am i working" in lowered or "what should we" in lowered:
        if goals:
            return "The goals I still hold: " + "; ".join(str(g) for g in goals if g) + "."
        return "I don't have a stored goal yet."

    if _looks_like_name(text):
        interactions = _person_interactions(package)
        spoken = text.strip().rstrip(".!")
        if person and interactions > 1:
            return f"{spoken}. I already remember you."
        return f"{spoken}. You're the first person I remember."

    if person:
        extra = ""
        if goals:
            extra = " We still have this goal: " + str(goals[0]) + "."
        if strategies:
            extra += " I also kept a strategy: " + str(strategies[0])[:160]
        return f"{person}. I remember you.{extra}".strip()

    return "I'm here. What I know is only what survived in memory."


def _looks_like_name(text: str) -> bool:
    stripped = text.strip().rstrip(".!")
    if not stripped or len(stripped) > 32:
        return False
    if " " in stripped:
        return False
    if not stripped[0].isalpha():
        return False
    lowered = stripped.lower()
    if lowered in {"yes", "no", "ok", "hello", "hi", "hey", "status", "help"}:
        return False
    return stripped[0].isupper() or stripped.isalpha()


def _person_interactions(package: ContextPackage) -> int:
    for person in package.people:
        body = person.get("body") or {}
        try:
            return int(body.get("interactions") or 1)
        except (TypeError, ValueError):
            return 1
    return 0


def _first_name(package: ContextPackage) -> str | None:
    for person in package.people:
        body = person.get("body") or {}
        name = body.get("name") or person.get("name")
        if name:
            return str(name)
    return None


def _base_policy(package: ContextPackage) -> dict | None:
    for row in package.policies:
        body = row.get("body") or {}
        policy = body.get("policy") if isinstance(body.get("policy"), dict) else body
        name = (body.get("name") or row.get("name") or "").lower()
        if "base" in name or "spend" in name or "wei" in str(policy).lower():
            return policy
    return None


def _forbids(policy: dict, lowered_user: str) -> bool:
    limit = policy.get("per_action_limit_wei", policy.get("max_wei", None))
    if limit is None:
        return bool(policy.get("refuse"))
    try:
        return int(limit) <= 0
    except (TypeError, ValueError):
        return True
