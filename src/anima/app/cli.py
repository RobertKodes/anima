"""Anima CLI entry.

Default: graphical terminal UI (Hermes-class TUI).
`--cli` / `--plain`: classic REPL for scripts, tests, and pipes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from anima.config.schema import AnimaConfig, BrainConfig, load_config
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
    parser.add_argument("--ui", action="store_true", help="Open the graphical web companion")
    parser.add_argument("--yes", "-y", action="store_true", help="Non-interactive defaults for setup")
    parser.add_argument(
        "verb",
        nargs="?",
        help="setup | doctor | chat | a /command (for example /status)",
    )
    parser.add_argument("rest", nargs="*", help="Extra words for chat or /commands")
    args = parser.parse_args(argv)

    if args.verb == "setup" or args.init:
        from anima.app.setup import run_setup

        return run_setup(args.data, yes=args.yes or args.init, brain=args.brain, model=args.model)

    cfg = load_config(args.config, args.data)
    if args.amnesia:
        cfg.amnesia = True
    if args.brain:
        _apply_brain_override(cfg, args.brain, args.model)
    elif args.model and cfg.brains:
        cfg.brains[0].model = args.model

    if args.verb == "doctor":
        runtime = Runtime(cfg, amnesia=cfg.amnesia)
        from anima.app.commands import cmd_doctor

        reply = cmd_doctor(runtime, [])
        Console().print(reply.text)
        return 0 if reply.data.get("ok") else 1

    runtime = Runtime(cfg, amnesia=cfg.amnesia)

    if args.ui:
        from anima.ui.web import serve

        return serve(runtime)

    once = args.once
    if args.verb == "chat" and args.rest:
        once = " ".join(args.rest)
    elif args.verb and args.verb.startswith("/"):
        once = " ".join([args.verb, *args.rest]).strip()
    elif args.verb and args.verb not in {"chat"}:
        once = " ".join([args.verb, *args.rest]).strip()

    if once:
        return _run_once(runtime, once)
    if args.cli or (not args.tui and (not sys.stdin.isatty() or not sys.stdout.isatty())):
        return _run_plain(runtime)
    from anima.app.tui import run_tui

    run_tui(runtime)
    return 0


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


def _run_once(runtime: Runtime, line: str) -> int:
    console = Console()
    boot = runtime.boot()
    _print_boot(console, runtime, boot)
    reply = runtime.handle(line)
    _print_reply(console, reply)
    return 0


def _run_plain(runtime: Runtime) -> int:
    console = Console()
    boot = runtime.boot()
    _print_boot(console, runtime, boot)
    _print_reply(console, boot)
    if not sys.stdin.isatty():
        for line in sys.stdin:
            if not line.strip():
                continue
            _print_reply(console, runtime.handle(line.rstrip("\n")))
        return 0
    console.print("[dim]Type /help · tab is TUI-only · leave with Ctrl-D[/]")
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
        _print_reply(console, runtime.handle(line))


def _print_boot(console: Console, runtime: Runtime, boot) -> None:
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
