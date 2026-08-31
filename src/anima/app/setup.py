"""First-run setup and a public-facing doctor. Identity still lives in Sibyl."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from anima.config.schema import AnimaConfig, BrainConfig, default_config, load_config, save_config


def doctor_report(cfg: AnimaConfig) -> list[dict[str, Any]]:
    rows = []
    rows.append(_ok("python", True, "3.10+ required; this process is running"))
    try:
        import sibyl_memory_client

        rows.append(_ok("sibyl-memory-client", True, getattr(sibyl_memory_client, "__version__", "installed")))
    except Exception as exc:
        rows.append(_ok("sibyl-memory-client", False, str(exc)))
    db_parent = cfg.sibyl_db.parent
    writable = db_parent.exists() and os_writable(db_parent)
    rows.append(_ok("sibyl path", writable, str(cfg.sibyl_db)))
    rows.append(_ok("ollama", _http_ok("http://127.0.0.1:11434/api/tags"), "localhost:11434"))
    rows.append(_ok("llama.cpp", _http_ok("http://127.0.0.1:8080/v1/models") or bool(shutil.which("llama-server")), "llama-server on :8080 or on PATH"))
    rows.append(_ok("ffmpeg", bool(shutil.which("ffmpeg")), shutil.which("ffmpeg") or "not on PATH"))
    rows.append(_ok("instinct brain", True, "always available — tests and first-run work offline"))
    from anima.base.adapter import base_crypto_available, wallet_creation_available

    crypto_ok, crypto_detail = base_crypto_available()
    wallet_ok, wallet_detail = wallet_creation_available()
    rows.append(
        _ok(
            "base wallet",
            wallet_ok,
            "eth-keys ready (dry-run wallets)" if wallet_ok else f"unavailable ({wallet_detail})",
        )
    )
    rows.append(
        _ok(
            "base signing",
            crypto_ok or cfg.base.dry_run,
            "eth-account ready (live broadcast)"
            if crypto_ok
            else (
                f"unavailable ({crypto_detail}); dry-run still works"
                if cfg.base.dry_run
                else f"unavailable ({crypto_detail})"
            ),
        )
    )
    wallet = Path(cfg.base.wallet_path).expanduser() if cfg.base.wallet_path else None
    if wallet and wallet.is_file():
        if os.name == "nt":
            rows.append(_ok("wallet file", True, f"{wallet} exists (Windows: Unix perms not enforced)"))
        else:
            mode = oct(wallet.stat().st_mode & 0o777)
            rows.append(_ok("wallet file", mode in {"0o600", "0o400"}, f"{wallet} perms {mode}"))
    else:
        rows.append(_ok("wallet file", True, "not created yet (safe default)"))
    rows.append(_ok("mainnet locked", not cfg.base.mainnet_enabled, "Base Sepolia / dry-run until you opt in"))
    from anima.memory.factory import open_memory
    from anima.memory.sibyl_adapter import SibylAdapter
    from anima.memory.sibyl_credentials import resolve_sibyl_auth, sibyl_cli_on_path

    auth = resolve_sibyl_auth(cfg)
    memory = open_memory(cfg)
    if isinstance(memory, SibylAdapter):
        health = memory.health()
        tier = health.get("tier") or auth.get("tier") or "free"
        cap_detail = f"tier={tier}, db={health.get('path')}"
        free = health.get("free_tier") or {}
        if isinstance(free, dict) and free.get("cap_bytes"):
            used = free.get("used_bytes") or health.get("bytes") or 0
            cap_detail += f", cap {used}/{free['cap_bytes']} bytes"
        rows.append(_ok("sibyl store", health.get("ok", False), cap_detail))
        memory.close()
    else:
        rows.append(_ok("sibyl store", False, "amnesia mode — retrieval disabled"))
    cli = sibyl_cli_on_path()
    rows.append(
        _ok(
            "sibyl CLI",
            cli is not None,
            cli or "pip install sibyl-memory-cli[mcp] · then sibyl init for Pro",
        )
    )
    if auth.get("account_id"):
        rows.append(_ok("sibyl Pro auth", True, f"account {str(auth['account_id'])[:8]}…"))
    else:
        rows.append(_ok("sibyl Pro auth", True, "optional — free tier local SQLite works"))
    rows.append(_ok("built-in MCP", True, "anima-sibyl (search, recent, self, people) in-process"))
    return rows


def os_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".anima-write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def _ok(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _http_ok(url: str) -> bool:
    try:
        with httpx.Client(timeout=0.6) as client:
            return client.get(url).status_code < 500
    except Exception:
        return False


def run_setup(data_dir: Path | None = None, *, yes: bool = False, brain: str | None = None, model: str | None = None) -> int:
    console = Console()
    cfg = default_config(data_dir)
    console.print(
        Panel(
            "[bold #e8a04a]ANIMA[/]\none being · many brains · memory is Sibyl\n\n"
            "This writes local config. It does [bold]not[/] invent a personality.\n"
            "The being is born the first time you talk to it.",
            border_style="#c45c26",
        )
    )
    ollama = _http_ok("http://127.0.0.1:11434/api/tags")
    llama = _http_ok("http://127.0.0.1:8080/v1/models")
    console.print(f"Ollama ........ {'found' if ollama else 'not running'}")
    console.print(f"llama.cpp ..... {'found' if llama else 'not running'}")
    console.print("Instinct ...... always (offline, honest, for tests and first-run)")

    choice = brain
    if not choice:
        if yes:
            choice = "ollama" if ollama else "fake"
        else:
            default = "ollama" if ollama else "fake"
            choice = Prompt.ask(
                "Primary brain",
                choices=["fake", "ollama", "llama_cpp"],
                default=default,
            )
    model_id = model
    if choice == "ollama":
        model_id = model_id or "qwen3:1.7b"
        cfg.brains = [
            BrainConfig(
                id="qwen3-local",
                role="primary",
                provider="ollama",
                endpoint="http://127.0.0.1:11434/v1",
                model=model_id,
                capabilities=["conversation"],
            )
        ]
        cfg.primary_brain_id = "qwen3-local"
    elif choice == "llama_cpp":
        model_id = model_id or "local"
        cfg.brains = [
            BrainConfig(
                id="llama-local",
                role="primary",
                provider="llama_cpp",
                endpoint="http://127.0.0.1:8080/v1",
                model=model_id,
                capabilities=["conversation"],
            )
        ]
        cfg.primary_brain_id = "llama-local"
    else:
        cfg.brains = [
            BrainConfig(id="instinct", role="primary", provider="fake", model="instinct", capabilities=["conversation"])
        ]
        cfg.primary_brain_id = "instinct"

    if not yes:
        cfg.base.dry_run = Confirm.ask("Keep Base in dry-run (recommended until a Sepolia wallet is funded)?", default=True)
    path = save_config(cfg)
    console.print(f"\nWrote [bold]{path}[/]")
    console.print(f"Sibyl store: [bold]{cfg.sibyl_db}[/]")
    console.print("\nNext: [bold #e8a04a]anima[/]  — graphical CLI")
    console.print("      [bold]anima doctor[/] — check the local toolchain")
    console.print("      [bold]anima sibyl setup[/] — link Pro credentials (sibyl init first)")
    console.print("      [bold]anima --cli[/] — classic REPL")
    return 0
