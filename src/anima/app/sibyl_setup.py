"""Link Anima to Sibyl Memory — credentials, Pro tier, and CLI guidance."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from anima.config.schema import AnimaConfig, load_config, save_config
from anima.memory.factory import open_memory
from anima.memory.sibyl_adapter import SibylAdapter
from anima.memory.sibyl_credentials import (
    credential_paths,
    format_sibyl_status,
    resolve_sibyl_auth,
    sibyl_cli_on_path,
)


def run_sibyl_setup(
    data_dir: Path | None = None,
    *,
    yes: bool = False,
    tier: str | None = None,
) -> int:
    console = Console()
    cfg = load_config(None, data_dir)
    console.print(
        Panel(
            "[bold #e8a04a]Sibyl Memory[/]\n"
            "Identity lives here — not in markdown, not in the model weights.\n\n"
            "Anima reads and writes through sibyl_memory_client on every turn.",
            border_style="#c45c26",
        )
    )

    auth = resolve_sibyl_auth(cfg)
    dest = cfg.data_dir / "secrets" / "sibyl.json"
    dest.parent.mkdir(parents=True, exist_ok=True)

    copied = False
    for src in credential_paths(cfg):
        if src == dest or not src.is_file():
            continue
        if auth.get("account_id") and dest.is_file():
            break
        shutil.copy2(src, dest)
        console.print(f"Linked credentials from [bold]{src}[/] → {dest}")
        auth = resolve_sibyl_auth(cfg)
        copied = True
        break

    cli = sibyl_cli_on_path()
    if not auth.get("account_id"):
        console.print("\n[yellow]No Pro account linked yet.[/]")
        if cli:
            console.print("Run the official Sibyl CLI once on this machine:")
            console.print(f"  [bold]{cli} init[/]")
            console.print("Then re-run: [bold]anima sibyl setup[/]")
        else:
            console.print("Install the Sibyl CLI:")
            console.print("  [bold]pip install sibyl-memory-cli[mcp][/]")
            console.print("Then: [bold]sibyl init[/]  and  [bold]anima sibyl setup[/]")
        console.print("\nFree tier works without init — local SQLite only, 256 KB cap.")
    elif copied:
        console.print(f"[green]Pro credentials ready[/] at {dest}")

    if tier:
        cfg.sibyl_tier = tier
        save_config(cfg)
        console.print(f"Set sibyl_tier = {tier!r} in config")

    memory = open_memory(cfg)
    if isinstance(memory, SibylAdapter):
        health = memory.health()
        console.print("\n" + format_sibyl_status(cfg, health))
        memory.close()
    return 0 if auth.get("account_id") or not cli else 0


def try_sibyl_init(non_interactive: bool = False) -> str | None:
    """Run `sibyl init` when CLI is present and user has a TTY."""
    cli = sibyl_cli_on_path()
    if not cli:
        return None
    try:
        subprocess.run([cli, "init"], check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return cli
