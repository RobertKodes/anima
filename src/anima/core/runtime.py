"""The organism: binds Sibyl, brains, tools, Base, and development into one identity."""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from typing import Any

from anima.base.adapter import BaseAdapter
from anima.base.policy import ActionRequest
from anima.cognition.providers.base import stream_brain
from anima.cognition.providers.fake import InstinctBrain, decide as instinct_decide
from anima.cognition.registry import BrainRegistry
from anima.cognition.router import route
from anima.config.schema import AnimaConfig, BrainConfig
from anima.core.context import ContextPackage
from anima.core.events import DecisionTrace, Intent, Reply, StreamPart, TraceItem
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
from anima.mcp.registry import McpRegistry
from anima.tools.permissions import may
from anima.tools.registry import CapabilityRegistry
from anima.tools.web import (
    crawl_site,
    explore_site,
    extract_url,
    fetch_url,
    format_crawl,
    format_explore,
    format_fetch,
)


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
        self._apply_capability_grants()
        self.mcp = McpRegistry(cfg)
        self.base = BaseAdapter(cfg.base)
        self.session_messages: list[tuple[str, str]] = []
        self._birth_done = False

    def _apply_capability_grants(self) -> None:
        grants = {
            "shell": self.cfg.allow_shell,
            "web_fetch": self.cfg.allow_web_fetch,
            "web_crawl": self.cfg.allow_web_crawl,
            "explore": self.cfg.allow_explore,
        }
        for cap_id, enabled in grants.items():
            if enabled:
                self.capabilities.grant(cap_id)

    def _experience_hint(self) -> str:
        exp_id = self.cfg.active_experience_id
        if not exp_id:
            return ""
        from anima.experiences.marketplace import load_experience

        pack = load_experience(self.cfg, exp_id)
        if pack is None:
            return ""
        persona = pack.manifest.personality
        parts = [f"Active experience pack: {pack.manifest.title} ({pack.id})."]
        if persona.tone:
            parts.append(f"Tone: {persona.tone}")
        if pack.manifest.unique:
            parts.append(pack.manifest.unique)
        return " ".join(parts)

    def _system(self, package: ContextPackage) -> str:
        return system_preamble(package.amnesia, experience_hint=self._experience_hint())

    def grant_capability(self, cap_id: str, *, persist: bool = True) -> None:
        self.capabilities.grant(cap_id)
        flag_map = {
            "shell": "allow_shell",
            "web_fetch": "allow_web_fetch",
            "web_crawl": "allow_web_crawl",
            "explore": "allow_explore",
        }
        if persist and cap_id in flag_map:
            setattr(self.cfg, flag_map[cap_id], True)
            from anima.config.schema import save_config

            save_config(self.cfg)

    def revoke_capability(self, cap_id: str, *, persist: bool = True) -> None:
        self.capabilities.revoke(cap_id)
        flag_map = {
            "shell": "allow_shell",
            "web_fetch": "allow_web_fetch",
            "web_crawl": "allow_web_crawl",
            "explore": "allow_explore",
        }
        if persist and cap_id in flag_map:
            setattr(self.cfg, flag_map[cap_id], False)
            from anima.config.schema import save_config

            save_config(self.cfg)

    def run_web_skill(self, kind: str, url: str) -> tuple[str, list[TraceItem]]:
        cap_id = kind
        allowed, reason = may(self.capabilities, cap_id)
        if not allowed:
            return f"Skill `{cap_id}` is off. Try `/capabilities grant {cap_id}` or `anima onboard`.", []
        if kind == "web_fetch":
            result = fetch_url(url)
            text = format_fetch(result)
        elif kind == "web_crawl":
            result = crawl_site(url)
            text = format_crawl(result)
        elif kind == "explore":
            result = explore_site(url)
            text = format_explore(result)
        else:
            return f"Unknown web skill {kind!r}.", []
        traces = [TraceItem("tool", cap_id, url, text[:160])]
        if not self.amnesia:
            record_capability(self.memory, cap_id, "used", url)
        return text, traces

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

    def iter_handle(self, raw: str) -> Iterator[StreamPart]:
        text = raw.rstrip("\n")
        if text.startswith("/"):
            from anima.app.commands import dispatch

            yield StreamPart("done", reply=dispatch(self, text))
            return

        yield StreamPart("status", "remembering…")
        turn = self._prepare_turn(text)
        yield StreamPart("status", "thinking…")

        thinking_parts: list[str] = []
        reply_parts: list[str] = []
        started = time.perf_counter()

        if turn["reply_mode"] == "stream" and turn.get("stream_prompt"):
            for chunk in self._stream_prompt(turn["stream_prompt"], turn["package"], turn["brain_id"]):
                if chunk.kind == "think":
                    thinking_parts.append(chunk.text)
                    yield StreamPart("think", chunk.text)
                else:
                    reply_parts.append(chunk.text)
                    yield StreamPart("token", chunk.text)
            reply_text = "".join(reply_parts).strip()
            used_instinct = False
            latency = int((time.perf_counter() - started) * 1000)
            if not reply_text:
                reply_text, latency, used_instinct = turn["fallback_fn"]()
        elif turn["reply_mode"] == "instinct":
            for part in self._stream_instinct(text, turn["package"]):
                reply_parts.append(part.text)
                yield part
            reply_text = "".join(reply_parts).strip()
            used_instinct = True
            latency = int((time.perf_counter() - started) * 1000)
        else:
            reply_text, latency, used_instinct = turn["fallback_fn"]()
            yield StreamPart("token", reply_text)

        if turn.get("post_process"):
            reply_text = turn["post_process"](reply_text)

        trace = DecisionTrace(
            intent=turn["intent"].kind,
            brain_id="instinct" if used_instinct else turn["brain_id"],
            memories=turn["mem_traces"],
            tools=[TraceItem("router", turn["brain_id"], turn["decision"].reason), *turn["tool_traces"]],
            policy="; ".join(turn["notices"]),
            amnesia=self.amnesia,
        )
        if not self.amnesia:
            record_experience(
                self.memory,
                text,
                reply_text,
                turn["intent"].kind,
                trace.brain_id,
                extra={"route": turn["decision"].reason},
            )
            record_brain_outcome(self.memory, trace.brain_id, turn["intent"].kind, True, latency)
            save_last_trace(self.memory, trace.as_dict())
        self.session_messages.append(("user", text))
        self.session_messages.append(("being", reply_text))
        yield StreamPart("done", reply=Reply(text=reply_text, traces=trace, notices=turn["notices"]))

    def chat(self, user_text: str) -> Reply:
        reply: Reply | None = None
        for part in self.iter_handle(user_text):
            if part.kind == "done" and part.reply is not None:
                reply = part.reply
        assert reply is not None
        return reply

    def _prepare_turn(self, user_text: str) -> dict[str, Any]:
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
        tool_traces: list[TraceItem] = []
        stream_prompt: str | None = None
        reply_mode = "stream"
        fallback_fn = lambda: self._think(user_text, package, brain_id, decision.bounded)
        post_process = None
        brain: object = self.instinct

        if intent.kind in {"web_fetch", "web_crawl", "explore"}:
            url = intent.slots.get("url") or extract_url(user_text)
            if not url:
                reply_mode = "instant"
                fallback_fn = lambda: ("I need a URL. Example: /fetch https://example.com", 1, True)
            else:
                web_text, tool_traces = self.run_web_skill(intent.kind, url)
                if web_text.startswith("Skill `"):
                    reply_mode = "instant"
                    fallback_fn = lambda: (web_text, 1, True)
                else:
                    stream_prompt = (
                        package.as_prompt()
                        + "\n\nWEB SKILL OUTPUT (use this; do not invent beyond it):\n"
                        + web_text
                        + "\n\nUSER:\n"
                        + user_text
                    )
                    fallback_fn = lambda: self._complete_prompt(stream_prompt, package, brain_id, fallback=web_text)
        else:
            stream_prompt = self._build_prompt(user_text, package, decision.bounded)
            try:
                brain = self.registry.get(brain_id)
            except KeyError:
                brain = self.instinct
            if isinstance(brain, InstinctBrain):
                reply_mode = "instinct"
                stream_prompt = None

        if intent.kind == "base_action" and not self.amnesia:
            action_reply, action_notice = self._maybe_base(user_text, package, confirm=False)

            def _apply_base(text: str) -> str:
                out = action_reply if action_reply else text
                return out

            post_process = _apply_base
            if action_notice:
                notices.append(action_notice)

        return {
            "intent": intent,
            "notices": notices,
            "mem_traces": mem_traces,
            "brain_id": brain_id,
            "decision": decision,
            "tool_traces": tool_traces,
            "stream_prompt": stream_prompt,
            "fallback_fn": fallback_fn,
            "post_process": post_process,
            "package": package,
            "reply_mode": reply_mode,
        }

    def _build_prompt(self, user_text: str, package: ContextPackage, bounded: bool) -> str:
        context = package.as_prompt()
        if bounded:
            bounded_pkg = ContextPackage(
                amnesia=package.amnesia,
                strategies=package.strategies,
                knowledge=package.knowledge,
                query=package.query,
            )
            context = bounded_pkg.as_prompt() + "\n(Bounded specialist context: identity withheld.)"
        return context + "\n\nUSER:\n" + user_text

    def _stream_prompt(self, prompt: str, package: ContextPackage, brain_id: str):
        system = self._system(package)
        try:
            brain = self.registry.get(brain_id)
        except KeyError:
            brain = self.instinct
        yield from stream_brain(brain, prompt, system=system)

    def _stream_instinct(self, user_text: str, package: ContextPackage) -> Iterator[StreamPart]:
        text = instinct_decide(user_text, package)
        for word in text.split():
            yield StreamPart("token", word + " ")

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

    def _complete_prompt(
        self, prompt: str, package: ContextPackage, brain_id: str, *, fallback: str = ""
    ) -> tuple[str, int, bool]:
        system = self._system(package)
        try:
            brain = self.registry.get(brain_id)
        except KeyError:
            brain = self.instinct
        if isinstance(brain, InstinctBrain):
            return fallback or "Done.", 1, True
        result = brain.complete(prompt, system=system)
        if result.ok and result.text.strip():
            return result.text.strip(), result.latency_ms, False
        return fallback or "I could not summarize that page.", result.latency_ms or 1, True

    def _think(self, user_text: str, package: ContextPackage, brain_id: str, bounded: bool) -> tuple[str, int, bool]:
        system = self._system(package)
        prompt = self._build_prompt(user_text, package, bounded)

        try:
            brain = self.registry.get(brain_id)
        except KeyError:
            brain = self.instinct
        if isinstance(brain, InstinctBrain):
            return instinct_decide(user_text, package), 1, True
        result = brain.complete(prompt, system=system)
        if result.ok and result.text.strip():
            return result.text.strip(), result.latency_ms, False
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
    if name and (_is_name_introduction(stripped) or len(stripped.split()) <= 4):
        return Intent("remember_person", stripped, {"name": name, "note": stripped})
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
    if any(
        phrase in lowered
        for phrase in ("who am i", "do you remember me", "what's my name", "what is my name")
    ):
        return Intent("ask_memory", stripped, {})
    url = extract_url(stripped)
    if url:
        if any(word in lowered for word in ("crawl", "spider", "walk the site")):
            return Intent("web_crawl", stripped, {"url": url})
        if any(word in lowered for word in ("explore", "links on", "map this", "what links")):
            return Intent("explore", stripped, {"url": url})
        if any(
            word in lowered
            for word in ("fetch", "read", "open", "get", "summarize", "look at", "check", "browse", "visit")
        ):
            return Intent("web_fetch", stripped, {"url": url})
    return Intent("chat", stripped, {})


def _is_name_introduction(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("i am ", "i'm ", "my name is ", "call me "))


def _extract_name(text: str) -> str | None:
    patterns = [
        r"(?:i am|i'm|my name is|call me)\s+([a-zA-Z][a-zA-Z'-]{0,29})",
        r"^([a-zA-Z][a-zA-Z'-]{0,29})$",
    ]
    skip = {"a", "an", "the", "your", "maker", "hello", "hi", "hey"}
    for pattern in patterns:
        match = re.search(pattern, text.strip(), re.I)
        if not match:
            continue
        raw = match.group(1).strip().strip(".,!?")
        if not raw or raw.lower() in skip:
            continue
        return raw[0].upper() + raw[1:] if len(raw) > 1 else raw.upper()
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
