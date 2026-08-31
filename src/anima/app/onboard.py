"""Guided onboarding: detect brains, live-probe, then write config."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from anima.cognition.cloud import CLOUD_PRESETS, brain_config_from_cloud, preset_ids
from anima.cognition.registry import build_brain
from anima.config.schema import AnimaConfig, BrainConfig, config_exists, default_config, load_config, save_config
from anima.config.secrets import save_brain_secret, secret_configured

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
    auth_mode: str = "none"
    secret_id: str = ""
    env_var: str = ""
    cost_class: str = "local"
    cloud_preset: str = ""


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


def candidate_to_config(candidate: BrainCandidate) -> BrainConfig:
    return BrainConfig(
        id=candidate.brain_id,
        role="primary",
        provider=candidate.provider,  # type: ignore[arg-type]
        endpoint=candidate.endpoint,
        model=candidate.model,
        capabilities=["conversation"],
        auth_mode=candidate.auth_mode,  # type: ignore[arg-type]
        secret_id=candidate.secret_id or candidate.brain_id,
        env_var=candidate.env_var,
        cost_class=candidate.cost_class,
    )


def probe_brain(candidate: BrainCandidate, *, data_dir: Path | None = None, skip: bool = False) -> dict[str, Any]:
    if skip or candidate.provider == "fake":
        return {
            "ok": True,
            "provider": candidate.provider,
            "model": candidate.model,
            "latency_ms": 0,
            "text": "pong" if candidate.provider == "fake" else "",
            "skipped": skip,
        }
    root = data_dir or default_config().data_dir
    if candidate.auth_mode not in {"none", ""} and not secret_configured(
        root, candidate.secret_id or candidate.brain_id, candidate.auth_mode, candidate.env_var
    ):
        return {
            "ok": False,
            "provider": candidate.provider,
            "model": candidate.model,
            "error": "credentials missing for cloud brain",
            "skipped": False,
        }
    cfg = candidate_to_config(candidate)
    brain = build_brain(cfg, root)
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
    cfg.brains = [candidate_to_config(candidate)]
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
        auth_mode=primary.auth_mode,
        secret_id=primary.secret_id or primary.id,
        env_var=primary.env_var,
        cost_class=primary.cost_class,
    )


def run_onboard(
    data_dir: Path | None = None,
    *,
    non_interactive: bool = False,
    yes: bool = False,
    brain: str | None = None,
    model: str | None = None,
    cloud: str | None = None,
    auth: str | None = None,
    api_key: str | None = None,
    oauth_token: str | None = None,
    endpoint: str | None = None,
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
                "[dim]Inference first, then the rest of setup.[/]",
                border_style="#c45c26",
            )
        )
        if auto:
            console.print("[dim]Auto mode — detecting the best available brain…[/]")

    candidate: BrainCandidate | None = None
    probe: dict[str, Any] = {}

    try:
        if configured and existing is not None:
            current = candidate_from_config(existing)
            probe = probe_brain(current, data_dir=cfg.data_dir, skip=skip_probe or current.provider == "fake")
            if probe["ok"]:
                summary = _finish_summary(existing, current, probe, repaired=True)
                if json_output:
                    print(json.dumps(summary, indent=2))
                elif console is not None:
                    _print_verify_ok(console, current, probe, existing)
                return _maybe_launch(existing, launch=launch, json_output=json_output)

            if auto:
                candidate, probe = _auto_select(
                    brain,
                    model,
                    skip_probe=skip_probe,
                    cloud=cloud,
                    auth=auth,
                    api_key=api_key,
                    oauth_token=oauth_token,
                    endpoint=endpoint,
                    data_dir=cfg.data_dir,
                    console=console,
                )
                if candidate is None:
                    if json_output:
                        print(json.dumps({"ok": False, "error": "no working brain detected"}))
                    return 1
            elif console is not None:
                console.print(
                    f"[yellow]Current brain failed probe[/] ({current.label}): "
                    f"{probe.get('error') or probe.get('text')!r}"
                )
                if not Confirm.ask("Pick a new brain?", default=True):
                    return 1
                candidate = _pick_candidate(
                    console,
                    brain,
                    model,
                    cfg.data_dir,
                    cloud=cloud,
                    auth=auth,
                    api_key=api_key,
                    oauth_token=oauth_token,
                    endpoint=endpoint,
                    model_override=model,
                )
                if candidate is None:
                    console.print("[dim]Skipped. Run `anima onboard` when you're ready.[/]")
                    return 0
                probe = probe_brain(candidate, data_dir=cfg.data_dir, skip=skip_probe)
                if not probe["ok"] and candidate.provider != "fake":
                    console.print("[red]Probe failed.[/] Try Instinct, start Ollama, or run with --skip-probe.")
                    return 1
            else:
                return 1
        else:
            if auto:
                candidate, probe = _auto_select(
                    brain,
                    model,
                    skip_probe=skip_probe,
                    cloud=cloud,
                    auth=auth,
                    api_key=api_key,
                    oauth_token=oauth_token,
                    endpoint=endpoint,
                    data_dir=cfg.data_dir,
                    console=console,
                )
                if candidate is None:
                    if json_output:
                        print(json.dumps({"ok": False, "error": "no working brain detected"}))
                    return 1
            elif console is not None:
                candidate = _pick_candidate(
                    console,
                    brain,
                    model,
                    cfg.data_dir,
                    cloud=cloud,
                    auth=auth,
                    api_key=api_key,
                    oauth_token=oauth_token,
                    endpoint=endpoint,
                    model_override=model,
                )
                if candidate is None:
                    console.print("[dim]Skipped. Run `anima onboard` when you're ready.[/]")
                    return 0
                probe = probe_brain(candidate, data_dir=cfg.data_dir, skip=skip_probe)
                if not probe["ok"] and candidate.provider != "fake":
                    if Confirm.ask("Probe failed. Use Instinct (offline) instead?", default=True):
                        candidate = _instinct_candidate()
                        probe = probe_brain(candidate, data_dir=cfg.data_dir, skip=True)
                    else:
                        console.print("[dim]Skipped. Run `anima onboard` again when a model is ready.[/]")
                        return 1
            else:
                return 1

        apply_brain_candidate(cfg, candidate)
    except ValueError as exc:
        if json_output:
            print(json.dumps({"ok": False, "error": str(exc)}))
        elif console is not None:
            console.print(f"[red]{exc}[/]")
        return 1

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
        if auto and not launch:
            console.print("\n[bold]Tip:[/] run [bold #e8a04a]anima onboard --launch[/] to open the graphical CLI.")
    return _maybe_launch(cfg, launch=launch, json_output=json_output)


def _auto_select(
    brain: str | None,
    model: str | None,
    *,
    skip_probe: bool,
    cloud: str | None = None,
    auth: str | None = None,
    api_key: str | None = None,
    oauth_token: str | None = None,
    endpoint: str | None = None,
    data_dir: Path | None = None,
    console: Console | None = None,
) -> tuple[BrainCandidate | None, dict[str, Any]]:
    root = data_dir or default_config().data_dir

    if cloud:
        candidate = _build_cloud_candidate(
            root,
            cloud,
            auth=auth or "env",
            model=model,
            endpoint=endpoint,
            api_key=api_key,
            oauth_token=oauth_token,
            console=console,
        )
        probe = probe_brain(candidate, data_dir=root, skip=skip_probe)
        if probe["ok"] or skip_probe:
            return candidate, probe
        return None, probe

    if brain:
        candidate = _candidate_for_provider(brain, model)
        probe = probe_brain(candidate, data_dir=root, skip=skip_probe or candidate.provider == "fake")
        if probe["ok"] or skip_probe or candidate.provider == "fake":
            return candidate, probe
        return None, probe

    for candidate in detect_brain_candidates():
        if candidate.provider == "fake":
            continue
        if console is not None:
            console.print(f"[dim]Probing[/] {candidate.label} …")
        probe = probe_brain(candidate, data_dir=root, skip=False)
        if probe["ok"]:
            if console is not None:
                console.print(
                    f"[green]Using[/] {candidate.label} "
                    f"[dim]({probe.get('latency_ms', 0)} ms · {probe.get('text')!r})[/]"
                )
            return candidate, probe

    if console is not None:
        console.print("[yellow]No live brain responded. Falling back to Instinct (offline).[/]")
    instinct = _instinct_candidate()
    return instinct, probe_brain(instinct, data_dir=root, skip=True)


def _pick_candidate(
    console: Console,
    brain: str | None,
    model: str | None,
    data_dir: Path,
    *,
    cloud: str | None = None,
    auth: str | None = None,
    api_key: str | None = None,
    oauth_token: str | None = None,
    endpoint: str | None = None,
    model_override: str | None = None,
) -> BrainCandidate | None:
    if cloud:
        return _build_cloud_candidate(
            data_dir,
            cloud,
            auth=auth,
            model=model_override or model,
            endpoint=endpoint,
            api_key=api_key,
            oauth_token=oauth_token,
            console=console,
        )
    if brain:
        return _candidate_for_provider(brain, model)

    candidates = detect_brain_candidates()
    console.print("\n[bold]Local brains[/]")
    for idx, item in enumerate(candidates, start=1):
        mark = "auto" if item.provider != "fake" else "fallback"
        console.print(f"  {idx}. {item.label}  [dim]({mark})[/]")
    console.print("\n[bold]Cloud / API[/]")
    for idx, preset_id in enumerate(preset_ids(), start=len(candidates) + 1):
        preset = CLOUD_PRESETS[preset_id]
        console.print(f"  {idx}. {preset.label}  [dim](cloud)[/]")
    console.print("  s. Skip for now")

    default = "1" if candidates and candidates[0].provider != "fake" else str(len(candidates))
    choice = Prompt.ask("Pick a brain", default=default)
    if choice.lower() in {"s", "skip"}:
        return None
    try:
        index = int(choice) - 1
    except ValueError:
        return candidates[-1]
    if index < len(candidates):
        return candidates[index]
    preset_index = index - len(candidates)
    preset_id = preset_ids()[preset_index]
    return _build_cloud_candidate(data_dir, preset_id, console=console)


def _build_cloud_candidate(
    data_dir: Path,
    preset_id: str,
    *,
    auth: str | None = None,
    model: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
    oauth_token: str | None = None,
    console: Console | None = None,
) -> BrainCandidate:
    preset = CLOUD_PRESETS[preset_id]
    resolved_auth = auth
    if console is not None and not resolved_auth:
        resolved_auth = Prompt.ask(
            "Auth method",
            choices=["api_key", "oauth", "env"],
            default="api_key",
        )
    resolved_auth = resolved_auth or "api_key"

    resolved_model = model
    if console is not None and not resolved_model and preset_id == "custom":
        resolved_model = Prompt.ask("Model id")
    elif console is not None and not resolved_model and preset.default_model:
        resolved_model = Prompt.ask("Model", default=preset.default_model)

    resolved_endpoint = endpoint
    if console is not None and preset_id == "custom" and not resolved_endpoint:
        resolved_endpoint = Prompt.ask("Base URL (OpenAI-compatible)", default="https://api.openai.com/v1")

    brain_cfg = brain_config_from_cloud(
        preset_id,
        model=resolved_model,
        endpoint=resolved_endpoint,
        auth_mode=resolved_auth,  # type: ignore[arg-type]
    )

    if resolved_auth == "api_key":
        key = api_key
        if not key and console is not None:
            key = Prompt.ask("API key", password=True)
        if not key:
            import os

            key = os.environ.get(brain_cfg.env_var)
        if not key:
            raise ValueError(f"API key required (flag --api-key or env {brain_cfg.env_var})")
        save_brain_secret(data_dir, brain_cfg.id, "api_key", api_key=key)
    elif resolved_auth == "oauth":
        token = oauth_token
        if console is not None and preset.oauth_url:
            console.print(f"\n[dim]Open[/] {preset.oauth_url} [dim]and paste an access token.[/]")
        if not token and console is not None:
            token = Prompt.ask("OAuth access token", password=True)
        if not token:
            raise ValueError("OAuth token required (--oauth-token)")
        save_brain_secret(data_dir, brain_cfg.id, "oauth", access_token=token)
    elif resolved_auth == "env":
        import os

        if not os.environ.get(brain_cfg.env_var):
            if console is not None:
                console.print(f"[yellow]Set[/] {brain_cfg.env_var} [yellow]in your environment before starting Anima.[/]")
            else:
                raise ValueError(f"env var {brain_cfg.env_var} is not set")

    return BrainCandidate(
        provider="openai_compatible",
        brain_id=brain_cfg.id,
        model=brain_cfg.model,
        endpoint=brain_cfg.endpoint,
        label=f"{preset.label} · {brain_cfg.model}",
        detected=False,
        auth_mode=resolved_auth,
        secret_id=brain_cfg.secret_id or brain_cfg.id,
        env_var=brain_cfg.env_var,
        cost_class="cloud",
        cloud_preset=preset_id,
    )


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
