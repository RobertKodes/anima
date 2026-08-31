"""Slash commands shared by the graphical TUI and the plain REPL."""

from __future__ import annotations

import shlex
from typing import Callable

from anima.config.schema import BrainConfig
from anima.core.events import Reply
from anima.core.runtime import Runtime
from anima.memory.writer import remember_goal
from anima.memory.sibyl_adapter import (
    CAT_GOAL,
    CAT_PERSON,
    CAT_SELF,
    SELF_NAME,
)


Handler = Callable[[Runtime, list[str]], Reply]


def dispatch(runtime: Runtime, line: str) -> Reply:
    stripped = line.strip()
    if not stripped.startswith("/"):
        return runtime.chat(stripped)
    try:
        parts = shlex.split(stripped)
    except ValueError:
        parts = stripped.split()
    command = parts[0].lower()
    args = parts[1:]
    handler = COMMANDS.get(command)
    if handler is None:
        return Reply(text=f"Unknown command {command}. Try /help.")
    return handler(runtime, args)


def cmd_help(_runtime: Runtime, _args: list[str]) -> Reply:
    lines = ["Commands:"]
    for name, summary in HELP:
        lines.append(f"  {name:<22} {summary}")
    return Reply(text="\n".join(lines))


def cmd_status(runtime: Runtime, _args: list[str]) -> Reply:
    data = runtime.status_data()
    mem = data["memory"]
    lines = [
        f"Stage            {data['stage']}",
        f"Age (turns)      {data['age_turns']}",
        f"Sleep cycles     {data['sleep_cycles']}",
        f"Goals            {data['evidence'].get('goals', 0)}",
        f"Relationships    {data['evidence'].get('relationships', 0)}",
        f"Sibyl            {'connected' if mem.get('ok') else 'unavailable'}  {mem.get('path') or mem.get('reason')}",
        f"Primary brain    {data['primary']}",
        f"Base             {data['base'].get('network')}  dry_run={data['base'].get('dry_run')}  mode={data['base'].get('approval_mode')}",
        f"Amnesia          {data['amnesia']}",
    ]
    return Reply(text="\n".join(lines), data=data)


def cmd_memory(runtime: Runtime, args: list[str]) -> Reply:
    if not args or args[0] == "recent":
        events = runtime.memory.read_events(limit=12)
        if not events:
            return Reply(text="No experiences stored.")
        lines = ["Recent experiences:"]
        for event in events:
            lines.append(f"- {event.get('ts')}: {event.get('acted')}")
        return Reply(text="\n".join(lines), data={"events": events})
    if args[0] == "search":
        query = " ".join(args[1:]).strip()
        if not query:
            return Reply(text="Usage: /memory search <query>")
        hits = runtime.memory.search(query, limit=12)
        if not hits:
            return Reply(text=f"No memories matched {query!r}.")
        lines = [f"Memories for {query!r}:"]
        for hit in hits:
            lines.append(
                f"- [{hit.get('tier') or hit.get('category')}] {hit.get('name') or hit.get('key') or hit.get('id')}"
            )
        return Reply(text="\n".join(lines), data={"hits": hits})
    return Reply(text="Usage: /memory recent | /memory search <query>")


def cmd_self(runtime: Runtime, _args: list[str]) -> Reply:
    row = runtime.memory.get_entity(CAT_SELF, SELF_NAME)
    if not row:
        return Reply(text="No self-model in Sibyl. This being has not been born, or memory is off.")
    body = row.get("body") or {}
    lines = [
        f"Name             {body.get('name') or '(not chosen)'}",
        f"Description      {body.get('self_description')}",
        f"Sleep cycles     {body.get('sleep_cycles') or 0}",
        f"Known abilities  {', '.join(body.get('known_abilities') or [])}",
        f"Limitations      {', '.join(body.get('limitations') or [])}",
        "Evidence lives in Sibyl entity self/being — not in a markdown file.",
    ]
    return Reply(text="\n".join(lines), data=body)


def cmd_people(runtime: Runtime, _args: list[str]) -> Reply:
    rows = runtime.memory.list_entities(CAT_PERSON, limit=50)
    if not rows:
        return Reply(text="No relationships stored yet.")
    lines = ["People I remember:"]
    for row in rows:
        body = row.get("body") or {}
        lines.append(f"- {body.get('name') or row.get('name')}: {body.get('summary')} (n={body.get('interactions')})")
    return Reply(text="\n".join(lines), data={"people": rows})


def cmd_goals(runtime: Runtime, args: list[str]) -> Reply:
    if args and args[0] == "add":
        title = " ".join(args[1:]).strip()
        if not title:
            return Reply(text="Usage: /goals add <title>")
        remember_goal(runtime.memory, title)
        return Reply(text=f"Goal stored: {title}")
    rows = runtime.memory.list_entities(CAT_GOAL, limit=50)
    if not rows:
        return Reply(text="No goals stored yet.")
    lines = ["Goals:"]
    for row in rows:
        body = row.get("body") or {}
        lines.append(f"- [{body.get('status')}] {body.get('title') or row.get('name')}: {body.get('summary')}")
    return Reply(text="\n".join(lines), data={"goals": rows})


def cmd_brains(runtime: Runtime, _args: list[str]) -> Reply:
    rows = runtime.registry.health()
    lines = [f"Primary: {runtime.registry.primary_id}", "Registered brains:"]
    for row in rows:
        mark = "*" if row.get("id") == runtime.registry.primary_id else " "
        ok = "up" if row.get("ok") else "down"
        lines.append(f"{mark} {row.get('id')}  {ok}  role={row.get('role')}  {row.get('model') or ''}")
    return Reply(text="\n".join(lines), data={"brains": rows})


def cmd_brain(runtime: Runtime, args: list[str]) -> Reply:
    if not args:
        return Reply(text="Usage: /brain add | /brain test <id> | /brain use <id>")
    verb = args[0]
    if verb == "add":
        parsed = _parse_kv(args[1:])
        brain_id = parsed.get("id") or parsed.get("name")
        if not brain_id:
            return Reply(text="Usage: /brain add id=coder provider=ollama model=qwen2.5-coder:7b role=coding")
        cfg = BrainConfig(
            id=brain_id,
            role=parsed.get("role", "specialist"),
            provider=parsed.get("provider", "ollama"),  # type: ignore[arg-type]
            endpoint=parsed.get("endpoint", ""),
            model=parsed.get("model", ""),
            activation=parsed.get("activation", "on_demand"),  # type: ignore[arg-type]
            capabilities=[c.strip() for c in parsed.get("capabilities", "code").split(",") if c.strip()],
        )
        runtime.add_brain(cfg, make_primary=parsed.get("primary") == "true")
        return Reply(text=f"Registered brain {cfg.id} ({cfg.provider}/{cfg.model}).")
    if verb == "test":
        if len(args) < 2:
            return Reply(text="Usage: /brain test <id>")
        brain_id = args[1]
        if brain_id not in runtime.registry.configs:
            return Reply(text=f"Unknown brain {brain_id!r}. Try /brains.")
        brain = runtime.registry.get(brain_id)
        health = brain.health()
        probe = brain.complete("Reply with the single word pong.", system="Be brief.")
        return Reply(
            text=f"health={health}\nprobe_ok={probe.ok} latency_ms={probe.latency_ms} text={probe.text!r} error={probe.error!r}"
        )
    if verb == "use":
        if len(args) < 2:
            return Reply(text="Usage: /brain use <id>")
        brain_id = args[1]
        if brain_id not in runtime.registry.configs:
            return Reply(text=f"Unknown brain {brain_id!r}. Try /brains.")
        runtime.swap_primary(brain_id)
        return Reply(text=f"Primary brain is now {brain_id}. Identity stays in Sibyl.")
    return Reply(text="Usage: /brain add | /brain test <id> | /brain use <id>")


def cmd_capabilities(runtime: Runtime, args: list[str]) -> Reply:
    if args and args[0] == "grant":
        if len(args) < 2:
            return Reply(text="Usage: /capabilities grant <web_fetch|web_crawl|explore|shell>")
        cap_id = args[1]
        try:
            runtime.grant_capability(cap_id)
        except KeyError:
            return Reply(text=f"Unknown capability {cap_id!r}. Try /skills.")
        return Reply(text=f"Granted {cap_id}. Saved to config.", notices=[f"{cap_id} granted"])
    if args and args[0] == "revoke":
        if len(args) < 2:
            return Reply(text="Usage: /capabilities revoke <id>")
        cap_id = args[1]
        try:
            runtime.revoke_capability(cap_id)
        except KeyError:
            return Reply(text=f"Unknown capability {cap_id!r}.")
        return Reply(text=f"Revoked {cap_id}. Saved to config.")
    lines = ["Capabilities:"]
    for item in runtime.capabilities.as_dicts():
        flag = "on" if item["granted"] else "off"
        lines.append(f"- {item['id']}: {item['title']} [{flag}] {item['summary']}")
    lines.append("\nGrant: /capabilities grant web_fetch")
    return Reply(text="\n".join(lines), data={"capabilities": runtime.capabilities.as_dicts()})


def cmd_skills(_runtime: Runtime, _args: list[str]) -> Reply:
    from anima.skills.catalog import SKILLS

    lines = ["Skills Anima can learn:"]
    for skill in SKILLS:
        lines.append(f"- {skill.title} ({skill.capability})")
        lines.append(f"  {skill.summary}")
        lines.append(f"  Command: {skill.slash}")
    lines.append("\nEnable during onboarding or: /capabilities grant web_fetch")
    return Reply(text="\n".join(lines))


def cmd_fetch(runtime: Runtime, args: list[str]) -> Reply:
    url = args[0] if args else ""
    if not url:
        return Reply(text="Usage: /fetch <url>")
    text, _ = runtime.run_web_skill("web_fetch", url)
    return Reply(text=text)


def cmd_crawl(runtime: Runtime, args: list[str]) -> Reply:
    url = args[0] if args else ""
    if not url:
        return Reply(text="Usage: /crawl <url>")
    text, _ = runtime.run_web_skill("web_crawl", url)
    return Reply(text=text)


def cmd_explore(runtime: Runtime, args: list[str]) -> Reply:
    url = args[0] if args else ""
    if not url:
        return Reply(text="Usage: /explore <url>")
    text, _ = runtime.run_web_skill("explore", url)
    return Reply(text=text)


def cmd_sleep(runtime: Runtime, _args: list[str]) -> Reply:
    return runtime.sleep()


def cmd_base(runtime: Runtime, args: list[str]) -> Reply:
    if not args or args[0] == "status":
        status = runtime.base.status()
        lines = [f"{key}: {value}" for key, value in status.items()]
        return Reply(text="\n".join(lines), data=status)
    if args[0] == "wallet":
        address = runtime.base.ensure_wallet()
        return Reply(text=f"Wallet address {address}. The key stays in {runtime.base.wallet_path}, never in Sibyl.")
    if args[0] == "action":
        parsed = _parse_kv(args[1:])
        intent = parsed.get("intent") or "sepolia-note"
        to = parsed.get("to") or runtime.base.address() or "0x0000000000000000000000000000000000000000"
        value_raw = parsed.get("value") or parsed.get("wei") or 0
        try:
            value = int(value_raw)
        except (TypeError, ValueError):
            return Reply(text=f"Invalid value {value_raw!r}. Use an integer wei amount.")
        confirm = parsed.get("yes") == "true" or "--yes" in args
        return runtime.execute_base(intent, to, value, confirm)
    return Reply(text="Usage: /base status | /base wallet | /base action intent=... to=0x... value=0 --yes")


def cmd_why(runtime: Runtime, _args: list[str]) -> Reply:
    return runtime.why()


def cmd_new_session(runtime: Runtime, _args: list[str]) -> Reply:
    runtime.new_session()
    return Reply(text="Inference session cleared. Sibyl memory is untouched.")


def cmd_amnesia(runtime: Runtime, args: list[str]) -> Reply:
    if args and args[0] in {"off", "end"}:
        if runtime.amnesia:
            return Reply(text="Restart Anima without --amnesia to return to the real store. Nothing was deleted.")
        return Reply(text="Amnesia is not active.")
    return Reply(
        text=(
            "Amnesia demo is a process flag, not a delete. Start with `anima --amnesia` "
            "to run without retrieval. The Sibyl file stays on disk."
        )
    )


def cmd_chat(runtime: Runtime, args: list[str]) -> Reply:
    return runtime.chat(" ".join(args))


def cmd_quit(_runtime: Runtime, _args: list[str]) -> Reply:
    return Reply(text="Still in Sibyl when you come back.", data={"quit": True})


def cmd_doctor(runtime: Runtime, _args: list[str]) -> Reply:
    from anima.app.setup import doctor_report

    report = doctor_report(runtime.cfg)
    lines = ["Anima doctor"]
    ok = True
    for row in report:
        mark = "ok" if row["ok"] else "FAIL"
        if not row["ok"]:
            ok = False
        lines.append(f"  [{mark}] {row['name']}: {row['detail']}")
    lines.append("Ready for public use." if ok else "Fix the FAIL rows before a demo.")
    return Reply(text="\n".join(lines), data={"doctor": report, "ok": ok})


def _parse_kv(args: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in args:
        if item in {"--yes", "-y"}:
            out["yes"] = "true"
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            out[key.lstrip("-")] = value
    return out


HELP = [
    ("/chat", "Talk to the being (default)."),
    ("/status", "Age, stage, memory health, brains, Base."),
    ("/memory search <q>", "Inspect Sibyl memories."),
    ("/memory recent", "Inspect recent experiences."),
    ("/self", "Inspectable self-model and evidence."),
    ("/people", "Known relationships."),
    ("/goals", "Active and completed goals."),
    ("/brains", "Registered cognitive models."),
    ("/brain add", "Register a local or cloud model."),
    ("/brain test <id>", "Health and capability probe."),
    ("/brain use <id>", "Switch primary brain; identity stays."),
    ("/capabilities", "Tools and permissions."),
    ("/capabilities grant <id>", "Enable web_fetch, web_crawl, explore, shell."),
    ("/skills", "Skills Anima can learn (web, explore)."),
    ("/fetch <url>", "Fetch and read a public page."),
    ("/crawl <url>", "Crawl same-site links."),
    ("/explore <url>", "Summarize a page and list links."),
    ("/sleep", "Consolidate recent life into Sibyl."),
    ("/base status", "Network, wallet, policy."),
    ("/base action ...", "Prepare or execute an approved action."),
    ("/why", "Which memories and brains shaped the last reply."),
    ("/new-session", "Clear inference context; keep Sibyl."),
    ("/amnesia-demo", "How to run without memory without deleting it."),
    ("/doctor", "Check Sibyl, brains, and the local toolchain."),
    ("/help", "This list."),
    ("/quit", "Leave. Memory stays in Sibyl."),
]


COMMANDS: dict[str, Handler] = {
    "/help": cmd_help,
    "/chat": cmd_chat,
    "/status": cmd_status,
    "/memory": cmd_memory,
    "/self": cmd_self,
    "/people": cmd_people,
    "/goals": cmd_goals,
    "/brains": cmd_brains,
    "/brain": cmd_brain,
    "/capabilities": cmd_capabilities,
    "/skills": cmd_skills,
    "/fetch": cmd_fetch,
    "/crawl": cmd_crawl,
    "/explore": cmd_explore,
    "/sleep": cmd_sleep,
    "/base": cmd_base,
    "/why": cmd_why,
    "/new-session": cmd_new_session,
    "/amnesia-demo": cmd_amnesia,
    "/doctor": cmd_doctor,
    "/quit": cmd_quit,
    "/exit": cmd_quit,
}

SLASH_PREFIXES = [
    "/help",
    "/status",
    "/memory recent",
    "/memory search ",
    "/self",
    "/people",
    "/goals",
    "/brains",
    "/brain add ",
    "/brain test ",
    "/brain use ",
    "/capabilities",
    "/capabilities grant ",
    "/skills",
    "/fetch ",
    "/crawl ",
    "/explore ",
    "/sleep",
    "/base status",
    "/base wallet",
    "/base action ",
    "/why",
    "/new-session",
    "/amnesia-demo",
    "/doctor",
    "/quit",
]
