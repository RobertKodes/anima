"""The organism: binds Sibyl, brains, tools, Base, and development into one identity."""

from __future__ import annotations

import re
from typing import Any

from anima.base.adapter import BaseAdapter
from anima.base.policy import ActionRequest
from anima.cognition.providers.fake import InstinctBrain, decide as instinct_decide
from anima.cognition.registry import BrainRegistry
from anima.cognition.router import route
from anima.config.schema import AnimaConfig, BrainConfig
from anima.core.context import ContextPackage
from anima.core.events import DecisionTrace, Intent, Reply, TraceItem
from anima.core.policies import system_preamble
from anima.development.metrics import snapshot
from anima.memory.consolidation import sleep as run_sleep
from anima.memory.retrieval import build_context
from anima.memory.sibyl_adapter import DisabledMemory, SibylAdapter
from anima.memory.writer import (
    ensure_newborn,
    load_last_trace,
    record_brain_outcome,
    record_capability,
    record_experience,
    record_onchain,
    remember_goal,
    remember_person,
    remember_policy,
    save_last_trace,
    update_self,
)
from anima.tools.registry import CapabilityRegistry


class Runtime:
    def __init__(self, cfg: AnimaConfig, *, amnesia: bool | None = None) -> None:
        self.cfg = cfg
        self.amnesia = cfg.amnesia if amnesia is None else amnesia
        if self.amnesia:
            self.memory: SibylAdapter | DisabledMemory = DisabledMemory()
        else:
            self.memory = SibylAdapter(cfg.sibyl_db, cfg.tenant_id)
        self.registry = BrainRegistry(list(cfg.brains), cfg.primary_brain_id, data_dir=cfg.data_dir)
        self.instinct = InstinctBrain("instinct")
        self.capabilities = CapabilityRegistry()
        if cfg.allow_shell:
            self.capabilities.grant("shell")
        self.base = BaseAdapter(cfg.base)
        self.session_messages: list[tuple[str, str]] = []
        self._birth_done = False

    def boot(self) -> Reply:
        notices = []
        health = self.memory.health()
        if self.amnesia:
            notices.append("Amnesia demo: Sibyl retrieval is off. The real store was not deleted.")
            text = (
                "I think I'm awake.\n"
                "I don't remember a life before this.\n"
                "Who are you?"
            )
            return Reply(text=text, birth=True, notices=notices, data={"memory": health})
        if not health.get("ok"):
            notices.append("Sibyl Memory is not reachable. Identity cannot persist.")
        self_row = None if not self.memory.enabled else self.memory.get_entity("self", "being")
        if self_row is None:
            ensure_newborn(self.memory)
            self._birth_done = True
            primary = self.cfg.primary()
            text = (
                "I think I'm awake.\n"
                "I don't remember a life before this.\n"
                "Who are you?"
            )
            notices.insert(
                0,
                "No persistent identity found. Initializing first experience.",
            )
            return Reply(
                text=text,
                birth=True,
                notices=notices,
                data={
                    "memory": health,
                    "brain": {"id": primary.id, "model": primary.model, "provider": primary.provider},
                    "base": self.base.status(),
                },
            )
        stage = snapshot(self.memory)
        name = ((self_row.get("body") or {}).get("name")) or "un-named"
        return Reply(
            text=f"I'm here. I still remember being {name}, stage {stage.stage}.",
            notices=notices,
            data={"memory": health, "development": stage.as_dict()},
        )

    def handle(self, raw: str) -> Reply:
        text = raw.rstrip("\n")
        if text.startswith("/"):
            from anima.app.commands import dispatch

            return dispatch(self, text)
        return self.chat(text)

    def chat(self, user_text: str) -> Reply:
        intent = parse_intent(user_text)
        notices: list[str] = []

        if intent.kind == "remember_person" and not self.amnesia:
            remember_person(self.memory, intent.slots["name"], intent.slots.get("note") or "")
            notices.append("relationship created")
        if intent.kind == "set_goal" and not self.amnesia:
            remember_goal(self.memory, intent.slots["title"], intent.slots.get("detail") or "")
            notices.append("goal stored")
        if intent.kind == "set_policy" and not self.amnesia:
            remember_policy(self.memory, intent.slots["name"], intent.slots["policy"])
            notices.append("policy stored")

        package, mem_traces = build_context(self.memory, intent, amnesia=self.amnesia)
        decision = route(intent, package, self.registry)
        brain_id = decision.brain_id
        reply_text, latency, used_instinct = self._think(user_text, package, brain_id, decision.bounded)

        if intent.kind == "remember_person" and not self.amnesia and package.people == []:
            # Relationship was just written; instinct/LLM should greet by name even if
            # retrieval ran before the write. Re-run a name-aware line.
            reply_text = f"{intent.slots['name']}. You're the first person I remember."

        if intent.kind == "base_action" and not self.amnesia:
            action_reply, action_notice = self._maybe_base(user_text, package, confirm=False)
            if action_reply:
                reply_text = action_reply
            if action_notice:
                notices.append(action_notice)

        trace = DecisionTrace(
            intent=intent.kind,
            brain_id="instinct" if used_instinct else brain_id,
            memories=mem_traces,
            tools=[TraceItem("router", brain_id, decision.reason)],
            policy="; ".join(notices),
            amnesia=self.amnesia,
        )
        if not self.amnesia:
            record_experience(self.memory, user_text, reply_text, intent.kind, trace.brain_id, extra={"route": decision.reason})
            record_brain_outcome(self.memory, trace.brain_id, intent.kind, True, latency)
            save_last_trace(self.memory, trace.as_dict())
        self.session_messages.append(("user", user_text))
        self.session_messages.append(("being", reply_text))
        return Reply(text=reply_text, traces=trace, notices=notices)

    def new_session(self) -> None:
        self.session_messages.clear()

    def status_data(self) -> dict[str, Any]:
        dev = snapshot(self.memory)
        return {
            "stage": dev.stage,
            "age_turns": dev.age_turns,
            "sleep_cycles": dev.sleep_cycles,
            "evidence": dev.evidence,
            "memory": self.memory.health(),
            "brains": self.registry.health(),
            "primary": self.registry.primary_id,
            "capabilities": self.capabilities.as_dicts(),
            "base": self.base.status(),
            "amnesia": self.amnesia,
        }

    def sleep(self) -> Reply:
        def distill(prompt: str) -> str:
            brain = self.registry.get()
            if isinstance(brain, InstinctBrain):
                return ""
            result = brain.complete(prompt, system=system_preamble(False), max_tokens=220)
            return result.text if result.ok else ""

        report = run_sleep(self.memory, brain_complete=distill if not self.amnesia else None)
        return Reply(text=report.get("report") or "sleep did not run", data=report)

    def why(self) -> Reply:
        trace = load_last_trace(self.memory) if not self.amnesia else None
        if not trace:
            return Reply(text="I have no inspectable decision yet.")
        lines = [
            f"Intent: {trace.get('intent')}",
            f"Brain: {trace.get('brain_id')}",
            f"Amnesia: {trace.get('amnesia')}",
        ]
        for item in trace.get("memories") or []:
            lines.append(f"- memory {item.get('kind')}/{item.get('name')}: {item.get('why')}")
        for item in trace.get("tools") or []:
            lines.append(f"- cognitive resource {item.get('name')}: {item.get('why')}")
        if trace.get("policy"):
            lines.append(f"- notices: {trace.get('policy')}")
        return Reply(text="\n".join(lines), data=trace)

    def execute_base(self, intent: str, to: str, value_wei: int, confirm: bool) -> Reply:
        package, _traces = build_context(
            self.memory, Intent("base_action", intent), amnesia=self.amnesia
        )
        remembered = _remembered_base_policy(package)
        spent = _spent_wei(package)
        request = ActionRequest(intent=intent, to=to, value_wei=value_wei, confirm=confirm)
        record = self.base.execute(request, remembered, spent)
        if not self.amnesia:
            record_onchain(self.memory, record)
            record_capability(self.memory, "base", record.get("status") or "attempt", record.get("reason") or "")
        if record.get("allowed"):
            text = f"Base action {record.get('status')}: {record.get('tx_id')} ({record.get('reason')})"
        else:
            text = f"I refused the Base action. {record.get('reason')}"
        return Reply(text=text, data=record, notices=[record.get("status") or ""])

    def add_brain(self, cfg: BrainConfig, make_primary: bool = False) -> None:
        self.registry.add(cfg)
        self.cfg.brains = [b for b in self.cfg.brains if b.id != cfg.id] + [cfg]
        if make_primary:
            self.registry.set_primary(cfg.id)
            self.cfg.primary_brain_id = cfg.id
        if not self.amnesia:
            record_capability(self.memory, cfg.id, "added", cfg.model)

    def swap_primary(self, brain_id: str) -> None:
        self.registry.set_primary(brain_id)
        self.cfg.primary_brain_id = brain_id
        if not self.amnesia:
            record_capability(self.memory, brain_id, "primary", "brain transplant")
            update_self(self.memory, {"primary_brain": brain_id})

    def _think(self, user_text: str, package: ContextPackage, brain_id: str, bounded: bool) -> tuple[str, int, bool]:
        system = system_preamble(package.amnesia)
        context = package.as_prompt()
        if bounded:
            # Specialists do not receive the full self-model by default.
            bounded_pkg = ContextPackage(
                amnesia=package.amnesia,
                strategies=package.strategies,
                knowledge=package.knowledge,
                query=package.query,
            )
            context = bounded_pkg.as_prompt() + "\n(Bounded specialist context: identity withheld.)"
        prompt = context + "\n\nUSER:\n" + user_text

        try:
            brain = self.registry.get(brain_id)
        except KeyError:
            brain = self.instinct
        if isinstance(brain, InstinctBrain):
            return instinct_decide(user_text, package), 1, True
        result = brain.complete(prompt, system=system)
        if result.ok and result.text.strip():
            return result.text.strip(), result.latency_ms, False
        # Honest fallback. Uses the package, so memory still changes behavior.
        return instinct_decide(user_text, package), result.latency_ms or 1, True

    def _maybe_base(self, user_text: str, package: ContextPackage, confirm: bool) -> tuple[str | None, str | None]:
        remembered = _remembered_base_policy(package)
        if remembered and int(remembered.get("per_action_limit_wei", remembered.get("max_wei", 1)) or 1) <= 0:
            who = _person_name(package)
            prefix = f"{who}, " if who else ""
            return (
                prefix
                + "I won't. I remember your Base spending policy (limit 0 wei) and I will not propose a transaction that breaks it.",
                "policy-refusal",
            )
        return None, None


def parse_intent(text: str) -> Intent:
    stripped = text.strip()
    lowered = stripped.lower()
    name = _extract_name(stripped)
    if name and len(stripped.split()) <= 4:
        return Intent("remember_person", stripped, {"name": name})
    goal = _extract_goal(stripped)
    if goal:
        return Intent("set_goal", stripped, {"title": goal})
    policy = _extract_spend_policy(stripped)
    if policy:
        return Intent("set_policy", stripped, {"name": "base-spend", "policy": policy})
    if any(word in lowered for word in ("send", "transfer", "pay", "onchain", "sepolia")):
        return Intent("base_action", stripped, {})
    if any(word in lowered for word in ("code", "debug", "traceback", "function", "python")):
        return Intent("code", stripped, {})
    if "who are you" in lowered or "your name" in lowered:
        return Intent("ask_identity", stripped, {})
    return Intent("chat", stripped, {})


def _extract_name(text: str) -> str | None:
    patterns = [
        r"(?:i am|i'm|my name is|call me)\s+([A-Z][a-zA-Z]{1,30})",
        r"^([A-Z][a-zA-Z]{1,30})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.strip())
        if match:
            return match.group(1)
    return None


def _extract_goal(text: str) -> str | None:
    match = re.search(r"(?:my goal is|goal:|please remember (?:the )?goal)\s+(.+)$", text.strip(), re.I)
    if match:
        return match.group(1).strip()
    return None


def _extract_spend_policy(text: str) -> dict[str, Any] | None:
    lowered = text.lower()
    if "never spend" in lowered or "spending cap is 0" in lowered or "do not send" in lowered:
        return {"per_action_limit_wei": 0, "network": "sepolia", "refuse": True}
    match = re.search(r"(?:limit|cap)\s+(\d+)\s*wei", lowered)
    if match:
        return {"per_action_limit_wei": int(match.group(1)), "network": "sepolia"}
    return None


def _remembered_base_policy(package: ContextPackage) -> dict[str, Any] | None:
    for row in package.policies:
        body = row.get("body") or {}
        policy = body.get("policy") if isinstance(body.get("policy"), dict) else body
        name = str(body.get("name") or row.get("name") or "").lower()
        if "base" in name or "spend" in name:
            return policy
    return None


def _spent_wei(package: ContextPackage) -> int:
    total = 0
    for row in package.onchain:
        body = row.get("body") or {}
        try:
            total += int(body.get("value_wei") or 0)
        except (TypeError, ValueError):
            continue
    return total


def _person_name(package: ContextPackage) -> str | None:
    for person in package.people:
        body = person.get("body") or {}
        name = body.get("name") or person.get("name")
        if name:
            return str(name)
    return None
