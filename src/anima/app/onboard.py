"""OpenClaw-style onboarding: detect brains, live-probe, then write config."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from anima.cognition.registry import build_brain
from anima.config.schema import AnimaConfig, BrainConfig, config_exists, default_config, load_config, save_config

PROBE_PROMPT = "Reply with the single word pong."
PROBE_SYSTEM = "Be brief. Reply with exactly one word."


@dataclass(frozen=True)
class BrainCandidate:
    provider: str
    brain_id: str
    model: str
    endpoint: str
    label: str
    detected: bool = True


def needs_onboarding(data_dir: Path | None = None, config_path: Path | None = None) -> bool:
    return not config_exists(config_path, data_dir)


def detect_brain_candidates() -> list[BrainCandidate]:
    candidates: list[BrainCandidate] = []
    for model in _ollama_models():
        candidates.append(
            BrainCandidate(
                provider="ollama",
                brain_id="qwen3-local" if model.startswith("qwen") else f"ollama-{model.replace(':', '-')}",
                model=model,
                endpoint="http://127.0.0.1:11434/v1",
                label=f"Ollama · {model}",
            )
        )
    if _http_ok("http://127.0.0.1:8080/v1/models"):
        candidates.append(
            BrainCandidate(
                provider="llama_cpp",
                brain_id="llama-local",
                model="local",
                endpoint="http://127.0.0.1:8080/v1",
                label="llama.cpp · localhost:8080",
            )
        )
    candidates.append(
        BrainCandidate(
            provider="fake",
            brain_id="instinct",
            model="instinct",
            endpoint="",
            label="Instinct · offline, always available",
            detected=True,
        )
    )
    return candidates


def probe_brain(candidate: BrainCandidate, *, skip: bool = False) -> dict[str, Any]:
    if skip or candidate.provider == "fake":
        return {
            "ok": True,
            "provider": candidate.provider,
            "model": candidate.model,
            "latency_ms": 0,
            "text": "pong" if candidate.provider == "fake" else "",
            "skipped": skip,
        }
    cfg = BrainConfig(
        id=candidate.brain_id,
        role="primary",
        provider=candidate.provider,  # type: ignore[arg-type]
        endpoint=candidate.endpoint,
        model=candidate.model,
        capabilities=["conversation"],
    )
    brain = build_brain(cfg)
    result = brain.complete(PROBE_PROMPT, system=PROBE_SYSTEM, max_tokens=16)
    text = (result.text or "").strip().lower()
    ok = result.ok and bool(text) and "pong" in text
    return {
        "ok": ok,
        "provider": candidate.provider,
        "model": candidate.model,
        "latency_ms": result.latency_ms,
        "text": result.text,
        "error": result.error,
        "skipped": False,
    }


def apply_brain_candidate(cfg: AnimaConfig, candidate: BrainCandidate) -> None:
    cfg.brains = [
        BrainConfig(
            id=candidate.brain_id,
            role="primary",
            provider=candidate.provider,  # type: ignore[arg-type]
            endpoint=candidate.endpoint,
            model=candidate.model,
            capabilities=["conversation"],
        )
    ]
    cfg.primary_brain_id = candidate.brain_id


def candidate_from_config(cfg: AnimaConfig) -> BrainCandidate:
    primary = cfg.primary()
    return BrainCandidate(
        provider=primary.provider,
        brain_id=primary.id,
        model=primary.model,
        endpoint=primary.endpoint,
        label=f"{primary.provider} · {primary.model or primary.id}",
        detected=False,
    )


def run_onboard(
    data_dir: Path | None = None,
    *,
    non_interactive: bool = False,
    yes: bool = False,
    brain: str | None = None,
    model: str | None = None,
    skip_probe: bool = False,
    json_output: bool = False,
    classic: bool = False,
    launch: bool = False,
) -> int:
    if classic:
        from anima.app.setup import run_setup

        return run_setup(data_dir, yes=non_interactive or yes, brain=brain, model=model)

    console = None if json_output else Console()
    auto = non_interactive or yes
    cfg = default_config(data_dir)
    configured = config_exists(data_dir=data_dir)
    existing = load_config(data_dir=data_dir) if configured else None

    if not json_output and console is not None:
        console.print(
            Panel(
                "[bold #e8a04a]ANIMA ONBOARD[/]\n"
                "Detect a brain · live-test it · save config · meet your being\n\n"
                "[dim]Like OpenClaw: inference first, then the rest of setup.[/]",
                border_style="#c45c26",
            )
        )

    if configured and existing is not None:
        current = candidate_from_config(existing)
        probe = probe_brain(current, skip=skip_probe or current.provider == "fake")
        if probe["ok"]:
            summary = _finish_summary(existing, current, probe, repaired=True)
            if json_output:
                print(json.dumps(summary, indent=2))
            elif console is not None:
                _print_verify_ok(console, current, probe, existing)
            return _maybe_launch(existing, launch=launch, json_output=json_output)

        if auto:
            candidate, probe = _auto_select(brain, model, skip_probe=skip_probe)
            if candidate is None:
                if json_output:
                    print(json.dumps({"ok": False, "error": "no working brain detected"}))
                return 1
        elif console is not None:
            console.print(
                f"[yellow]Current brain failed probe[/] ({current.label}): {probe.get('error') or probe.get('text')!r}"
            )
            if not Confirm.ask("Pick a new brain?", default=True):
                return 1
            candidate = _pick_candidate(console, brain, model)
            if candidate is None:
                console.print("[dim]Skipped. Run `anima onboard` when you're ready.[/]")
                return 0
            probe = probe_brain(candidate, skip=skip_probe)
            if not probe["ok"] and candidate.provider != "fake":
                console.print("[red]Probe failed.[/] Try Instinct, start Ollama, or run with --skip-probe.")
                return 1
        else:
            return 1
        apply_brain_candidate(cfg, candidate)
    else:
        if auto:
            candidate, probe = _auto_select(brain, model, skip_probe=skip_probe)
            if candidate is None:
                if json_output:
                    print(json.dumps({"ok": False, "error": "no working brain detected"}))
                return 1
        elif console is not None:
            candidate = _pick_candidate(console, brain, model)
            if candidate is None:
                console.print("[dim]Skipped. Run `anima onboard` when you're ready.[/]")
                return 0
            probe = probe_brain(candidate, skip=skip_probe)
            if not probe["ok"] and candidate.provider != "fake":
                if Confirm.ask("Probe failed. Use Instinct (offline) instead?", default=True):
                    candidate = _instinct_candidate()
                    probe = probe_brain(candidate, skip=True)
                else:
                    console.print("[dim]Skipped. Run `anima onboard` again when a model is ready.[/]")
                    return 1
        else:
            return 1
        apply_brain_candidate(cfg, candidate)

    if not auto and console is not None:
        cfg.base.dry_run = Confirm.ask(
            "Keep Base in dry-run (recommended until a Sepolia wallet is funded)?",
            default=True,
        )
    path = save_config(cfg)
    summary = _finish_summary(cfg, candidate, probe, config_path=path, repaired=configured)
    if json_output:
        print(json.dumps(summary, indent=2))
    elif console is not None:
        _print_success(console, cfg, candidate, probe, path)
    return _maybe_launch(cfg, launch=launch, json_output=json_output)


def _auto_select(
    brain: str | None,
    model: str | None,
    *,
    skip_probe: bool,
) -> tuple[BrainCandidate | None, dict[str, Any]]:
    if brain:
        candidate = _candidate_for_provider(brain, model)
        probe = probe_brain(candidate, skip=skip_probe or candidate.provider == "fake")
        if probe["ok"] or skip_probe or candidate.provider == "fake":
            return candidate, probe
        return None, probe

    for candidate in detect_brain_candidates():
        if candidate.provider == "fake":
            continue
        probe = probe_brain(candidate, skip=False)
        if probe["ok"]:
            return candidate, probe

    instinct = _instinct_candidate()
    return instinct, probe_brain(instinct, skip=True)


def _pick_candidate(console: Console, brain: str | None, model: str | None) -> BrainCandidate | None:
    if brain:
        return _candidate_for_provider(brain, model)

    candidates = detect_brain_candidates()
    console.print("\n[bold]Detected brains[/]")
    for idx, item in enumerate(candidates, start=1):
        mark = "auto" if item.provider != "fake" else "fallback"
        console.print(f"  {idx}. {item.label}  [dim]({mark})[/]")
    console.print("  s. Skip for now")

    default = "1" if candidates and candidates[0].provider != "fake" else str(len(candidates))
    choice = Prompt.ask("Pick a brain", default=default)
    if choice.lower() in {"s", "skip"}:
        return None
    try:
        index = int(choice) - 1
        return candidates[index]
    except (ValueError, IndexError):
        return candidates[-1]


def _candidate_for_provider(provider: str, model: str | None) -> BrainCandidate:
    if provider == "fake":
        return _instinct_candidate()
    if provider == "ollama":
        resolved = model or (_ollama_models()[0] if _ollama_models() else "qwen3:1.7b")
        return BrainCandidate(
            provider="ollama",
            brain_id="qwen3-local",
            model=resolved,
            endpoint="http://127.0.0.1:11434/v1",
            label=f"Ollama · {resolved}",
        )
    if provider == "llama_cpp":
        return BrainCandidate(
            provider="llama_cpp",
            brain_id="llama-local",
            model=model or "local",
            endpoint="http://127.0.0.1:8080/v1",
            label="llama.cpp · localhost:8080",
        )
    raise ValueError(f"unknown brain provider: {provider}")


def _instinct_candidate() -> BrainCandidate:
    return BrainCandidate(
        provider="fake",
        brain_id="instinct",
        model="instinct",
        endpoint="",
        label="Instinct · offline, always available",
    )


def _finish_summary(
    cfg: AnimaConfig,
    candidate: BrainCandidate,
    probe: dict[str, Any],
    *,
    config_path: Path | None = None,
    repaired: bool = False,
) -> dict[str, Any]:
    return {
        "ok": True,
        "repaired": repaired,
        "config_path": str(config_path or cfg.data_dir / "config.toml"),
        "sibyl_db": str(cfg.sibyl_db),
        "primary_brain_id": cfg.primary_brain_id,
        "brain": asdict(candidate),
        "probe": probe,
        "base_dry_run": cfg.base.dry_run,
    }


def _print_verify_ok(console: Console, candidate: BrainCandidate, probe: dict[str, Any], cfg: AnimaConfig) -> None:
    console.print(f"\n[green]Brain verified[/] · {candidate.label}")
    if probe.get("latency_ms"):
        console.print(f"[dim]Probe latency {probe['latency_ms']} ms · reply {probe.get('text')!r}[/]")
    console.print(f"[dim]Config[/] {cfg.data_dir / 'config.toml'}")
    console.print("\nNext: [bold #e8a04a]anima[/]  ·  [bold]anima doctor[/]  ·  [bold]anima --cli[/]")


def _print_success(
    console: Console,
    cfg: AnimaConfig,
    candidate: BrainCandidate,
    probe: dict[str, Any],
    path: Path,
) -> None:
    console.print(f"\n[green]Brain ready[/] · {candidate.label}")
    if probe.get("text"):
        console.print(f"[dim]Live probe reply[/] {probe['text']!r} ({probe.get('latency_ms', 0)} ms)")
    console.print(f"Wrote [bold]{path}[/]")
    console.print(f"Sibyl store: [bold]{cfg.sibyl_db}[/]")
    console.print("\nNext: [bold #e8a04a]anima[/]  — graphical CLI")
    console.print("      [bold]anima doctor[/] — check this machine")
    console.print("      [bold]anima onboard --classic[/] — config-only wizard")


def _maybe_launch(cfg: AnimaConfig, *, launch: bool, json_output: bool) -> int:
    if not launch or json_output:
        return 0
    from anima.core.runtime import Runtime
    from anima.app.tui import run_tui

    run_tui(Runtime(cfg))
    return 0


def _ollama_models() -> list[str]:
    try:
        with httpx.Client(timeout=1.5) as client:
            response = client.get("http://127.0.0.1:11434/api/tags")
            response.raise_for_status()
            names = [m["name"] for m in response.json().get("models", []) if m.get("name")]
    except Exception:
        return []
    preferred = [n for n in names if n == "qwen3:1.7b"]
    rest = [n for n in names if n != "qwen3:1.7b"]
    return preferred + rest


def _http_ok(url: str) -> bool:
    try:
        with httpx.Client(timeout=0.8) as client:
            return client.get(url).status_code < 500
    except Exception:
        return False
