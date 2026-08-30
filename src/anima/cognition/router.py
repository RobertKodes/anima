"""Inspectable cognitive router. Specialists get bounded context, never the whole self."""

from __future__ import annotations

from dataclasses import dataclass, field

from anima.config.schema import BrainConfig
from anima.core.context import ContextPackage
from anima.core.events import Intent
from anima.cognition.registry import BrainRegistry


CODE_HINTS = ("code", "debug", "function", "traceback", "python", "compile", "refactor")


@dataclass
class RouteDecision:
    brain_id: str
    reason: str
    specialist: bool = False
    bounded: bool = False
    candidates: list[str] = field(default_factory=list)


def route(intent: Intent, package: ContextPackage, registry: BrainRegistry) -> RouteDecision:
    primary = registry.primary_id
    specialists = [cfg for cfg in registry.list() if cfg.role != "primary" and cfg.activation == "on_demand"]

    if intent.kind == "code" or _wants_code(intent.raw):
        coder = _best_specialist(specialists, "code", package)
        if coder:
            return RouteDecision(
                brain_id=coder.id,
                reason="task looks like code; specialist registered",
                specialist=True,
                bounded=True,
                candidates=[coder.id, primary],
            )

    return RouteDecision(
        brain_id=primary,
        reason="primary brain",
        specialist=False,
        candidates=[primary],
    )


def _wants_code(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in CODE_HINTS)


def _best_specialist(specialists: list[BrainConfig], cap: str, package: ContextPackage) -> BrainConfig | None:
    matching = [cfg for cfg in specialists if cap in cfg.capabilities or cap in cfg.role]
    if not matching:
        return None
    ranked = _rank_by_memory(matching, package)
    return ranked[0] if ranked else matching[0]


def _rank_by_memory(configs: list[BrainConfig], package: ContextPackage) -> list[BrainConfig]:
    scores: dict[str, float] = {cfg.id: 0.0 for cfg in configs}
    for row in package.brain_perf:
        body = row.get("body") or {}
        brain_id = body.get("brain_id") or row.get("name")
        if brain_id not in scores:
            continue
        scores[brain_id] += float(body.get("successes") or 0) * 2
        scores[brain_id] -= float(body.get("failures") or 0)
        latency = float(body.get("latency_ms") or 0)
        if latency:
            scores[brain_id] -= latency / 10000.0
    for cfg in configs:
        if cfg.role == "primary":
            scores[cfg.id] += 0.1
        if cfg.cost_class == "local":
            scores[cfg.id] += 0.05
    return sorted(configs, key=lambda cfg: scores.get(cfg.id, 0.0), reverse=True)
