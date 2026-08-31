"""Anima CLI entry.

Default: graphical terminal UI (Hermes-class TUI).
`--cli` / `--plain`: classic REPL for scripts, tests, and pipes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from anima.config.schema import AnimaConfig, BrainConfig, config_exists, load_config

if TYPE_CHECKING:
    from anima.core.runtime import Runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="anima",
        description="A local-first persistent AI being. Memory is Sibyl. Models are brains.",
    )
    parser.add_argument("--data", type=Path, help="Data directory (default: ~/.anima or $ANIMA_HOME)")
    parser.add_argument("--config", type=Path, help="Path to config.toml")
    parser.add_argument("--cli", "--plain", action="store_true", help="Classic REPL instead of the graphical TUI")
    parser.add_argument("--tui", action="store_true", help="Force the graphical CLI (default on a TTY)")
    parser.add_argument("--amnesia", action="store_true", help="Run without Sibyl retrieval (does not delete the store)")
    parser.add_argument("-q", "--once", metavar="TEXT", help="Handle a single line and exit")
    parser.add_argument("--init", action="store_true", help="Write a default config and exit")
    parser.add_argument("--brain", choices=("fake", "ollama", "llama_cpp"), help="Override the primary brain provider")
    parser.add_argument("--model", help="Override the primary brain model id")
    parser.add_argument("--cloud", choices=("openai", "openrouter", "groq", "together", "custom"), help="Cloud brain preset")
    parser.add_argument("--auth", choices=("api_key", "oauth", "env"), help="Cloud auth method")
    parser.add_argument("--api-key", help="API key for cloud brain (prefer env vars in scripts)")
    parser.add_argument("--oauth-token", help="OAuth access token for cloud brain")
    parser.add_argument("--endpoint", help="Custom OpenAI-compatible base URL")
    parser.add_argument("--ui", action="store_true", help="Open the graphical web companion")
    parser.add_argument("--yes", "-y", action="store_true", help="Non-interactive defaults for setup/onboard")
    parser.add_argument("--non-interactive", action="store_true", help="Scripted onboard/setup (no prompts)")
    parser.add_argument("--json", action="store_true", help="Machine-readable onboard output")
    parser.add_argument("--skip-probe", action="store_true", help="Skip live brain probe during onboard")
    parser.add_argument("--classic", action="store_true", help="Config-only setup wizard (no live probe)")
    parser.add_argument("--launch", action="store_true", help="Open the graphical CLI after onboard")
    parser.add_argument(
        "--skills",
        metavar="LIST",
        help="Comma-separated skills for onboard: web_fetch,web_crawl,explore",
    )
    parser.add_argument(
        "verb",
        nargs="?",
        help="onboard | setup | doctor | sibyl | experiences | channel | chat | a /command (for example /status)",
    )
    parser.add_argument("rest", nargs="*", help="Extra words for chat or /commands")
    args = parser.parse_args(argv)

    if args.verb in {"onboard", "setup"} or args.init:
        from anima.app.onboard import run_onboard

        use_classic = args.classic or args.verb == "setup"
        return run_onboard(
            args.data,
            non_interactive=args.non_interactive or args.yes or args.init,
            yes=args.yes or args.init,
            brain=args.brain,
            model=args.model,
            cloud=args.cloud,
            auth=args.auth,
            api_key=args.api_key,
            oauth_token=args.oauth_token,
            endpoint=args.endpoint,
            skip_probe=args.skip_probe,
            json_output=args.json,
            classic=use_classic,
            launch=args.launch,
            skills=args.skills,
        )

    if _should_auto_onboard(args):
        from anima.app.onboard import run_onboard

        return run_onboard(
            args.data,
            non_interactive=args.yes,
            yes=args.yes,
            brain=args.brain,
            model=args.model,
            cloud=args.cloud,
            auth=args.auth,
            api_key=args.api_key,
            oauth_token=args.oauth_token,
            endpoint=args.endpoint,
            skip_probe=args.skip_probe,
            launch=True,
            skills=args.skills,
        )

    cfg = load_config(args.config, args.data)
    if args.amnesia:
        cfg.amnesia = True
    if args.brain:
        _apply_brain_override(cfg, args.brain, args.model)
    elif args.model and cfg.brains:
        cfg.brains[0].model = args.model

    if args.verb == "sibyl":
        from anima.app.sibyl_setup import run_sibyl_setup

        sub = args.rest[0] if args.rest else "setup"
        if sub in {"setup", "link"}:
            return run_sibyl_setup(args.data, yes=args.yes, tier=args.rest[1] if len(args.rest) > 1 else None)
        from anima.app.commands import cmd_sibyl
        from anima.core.runtime import Runtime

        runtime = Runtime(cfg, amnesia=cfg.amnesia)
        reply = cmd_sibyl(runtime, args.rest or ["status"])
        Console().print(reply.text)
        return 0

    if args.verb == "doctor":
        from anima.app.commands import cmd_doctor
        from anima.core.runtime import Runtime

        runtime = Runtime(cfg, amnesia=cfg.amnesia)
        reply = cmd_doctor(runtime, [])
        Console().print(reply.text)
        return 0 if reply.data.get("ok") else 1

    if args.verb == "experiences":
        from anima.app.commands import cmd_experiences
        from anima.core.runtime import Runtime

        runtime = Runtime(cfg, amnesia=cfg.amnesia)
        reply = cmd_experiences(runtime, args.rest)
        Console().print(reply.text)
        return 0

    if args.verb == "channel":
        from anima.channels.runner import run_channel
        from anima.core.runtime import Runtime

        if not args.rest:
            Console().print("Usage: anima channel telegram|discord")
            return 1
        runtime = Runtime(cfg, amnesia=cfg.amnesia)
        try:
            run_channel(runtime, args.rest[0].lower())
        except (RuntimeError, ValueError) as exc:
            Console().print(str(exc))
            return 1
        return 0

    from anima.core.runtime import Runtime

    runtime = Runtime(cfg, amnesia=cfg.amnesia)

    if args.ui:
        from anima.ui.web import serve

        return serve(runtime)

    once = args.once
    if args.verb == "chat" and args.rest:
        once = " ".join(args.rest)
    elif args.verb and args.verb.startswith("/"):
        once = " ".join([args.verb, *args.rest]).strip()
    elif args.verb and args.verb not in {"chat", "experiences", "channel"}:
        once = " ".join([args.verb, *args.rest]).strip()

    if once:
        return _run_once(runtime, once)
    if args.cli or (not args.tui and (not sys.stdin.isatty() or not sys.stdout.isatty())):
        return _run_plain(runtime)
    from anima.app.tui import run_tui

    run_tui(runtime)
    return 0


def _should_auto_onboard(args: argparse.Namespace) -> bool:
    if args.verb is not None or args.once or args.ui or args.amnesia or args.init:
        return False
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return False
    return needs_onboarding(args.data, args.config)


def needs_onboarding(data_dir: Path | None, config_path: Path | None) -> bool:
    return not config_exists(config_path, data_dir)


def _apply_brain_override(cfg: AnimaConfig, provider: str, model: str | None) -> None:
    defaults = {
        "fake": ("instinct", "instinct", ""),
        "ollama": ("qwen3-local", model or "qwen3:1.7b", "http://127.0.0.1:11434/v1"),
        "llama_cpp": ("llama-local", model or "local", "http://127.0.0.1:8080/v1"),
    }
    brain_id, resolved_model, endpoint = defaults[provider]
    cfg.brains = [
        BrainConfig(
            id=brain_id,
            role="primary",
            provider=provider,  # type: ignore[arg-type]
            model=resolved_model,
            endpoint=endpoint,
            capabilities=["conversation"],
        )
    ]
    cfg.primary_brain_id = brain_id


def _run_once(runtime: "Runtime", line: str) -> int:
    console = Console()
    boot = runtime.boot()
    _print_boot(console, runtime, boot)
    _stream_handle(console, runtime, line)
    return 0


def _run_plain(runtime: "Runtime") -> int:
    console = Console()
    boot = runtime.boot()
    _print_boot(console, runtime, boot)
    _print_reply(console, boot)
    if not sys.stdin.isatty():
        for line in sys.stdin:
            if not line.strip():
                continue
            _stream_handle(console, runtime, line.rstrip("\n"))
        return 0
    console.print("[dim]Type /help · live tokens below · anima (no --cli) for graphical TUI · Ctrl-D to leave[/]")
    while True:
        try:
            line = console.input("[bold #e8a04a]you[/] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]still in Sibyl when you come back.[/]")
            return 0
        if not line.strip():
            continue
        if line.strip() in {":q", "/quit", "/exit"}:
            return 0
        _stream_handle(console, runtime, line)


def _stream_handle(console: Console, runtime: "Runtime", line: str) -> None:
    """Print reply tokens as they arrive; show thinking when the brain exposes it."""
    reply = None
    wrote_think_header = False
    wrote_anima_prefix = False
    for part in runtime.iter_handle(line):
        if part.kind == "status" and sys.stdout.isatty():
            console.print(f"[dim]{part.text}[/]", end="\r")
        elif part.kind == "think":
            if not wrote_think_header:
                console.print("[dim italic]thinking[/]")
                wrote_think_header = True
            console.print(part.text, end="", style="dim italic")
        elif part.kind == "token":
            if wrote_think_header and not wrote_anima_prefix:
                console.print()
            if not wrote_anima_prefix:
                console.print("[bold]anima[/] ", end="")
                wrote_anima_prefix = True
            console.print(part.text, end="", highlight=False)
            console.file.flush()
        elif part.kind == "done" and part.reply is not None:
            reply = part.reply
    if wrote_anima_prefix:
        console.print()
    elif reply is not None:
        _print_reply(console, reply)
        return
    if reply is None:
        return
    for notice in reply.notices:
        console.print(f"[green]\\[{notice}][/]")


def _print_boot(console: Console, runtime: "Runtime", boot) -> None:
    data = runtime.status_data()
    mem = data["memory"]
    brain = data.get("primary")
    body = Text()
    body.append("No persistent identity found.\n" if boot.birth else "Continuing a life already underway.\n")
    body.append("Sibyl Memory ........ ", style="dim")
    body.append("connected\n" if mem.get("ok") else "unavailable\n", style="green" if mem.get("ok") else "red")
    body.append("Primary brain ....... ", style="dim")
    body.append(f"{brain}\n")
    body.append("Base ................. ", style="dim")
    body.append(f"{data['base'].get('network')} available\n")
    body.append("Capabilities ......... ", style="dim")
    body.append("conversation, memory\n")
    if boot.birth:
        body.append("\nInitializing first experience.")
    console.print(Panel(body, title="anima", border_style="#c45c26"))


def _print_reply(console: Console, reply) -> None:
    for notice in reply.notices:
        console.print(f"[green]\\[{notice}][/]")
    for line in reply.text.splitlines() or [reply.text]:
        console.print(f"[bold]anima[/] {line}")


if __name__ == "__main__":
    raise SystemExit(main())
