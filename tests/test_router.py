"""Router is inspectable, specialists are bounded, outcomes can rerank."""

from __future__ import annotations

from anima.cognition.registry import BrainRegistry
from anima.cognition.router import route
from anima.config.schema import BrainConfig
from anima.core.context import ContextPackage
from anima.core.events import Intent


def _registry() -> BrainRegistry:
    return BrainRegistry(
        [
            BrainConfig(id="instinct", role="primary", provider="fake", model="instinct"),
            BrainConfig(
                id="coder",
                role="coding",
                provider="fake",
                model="instinct",
                activation="on_demand",
                capabilities=["code", "debug"],
            ),
        ],
        primary_id="instinct",
    )


def test_specialist_only_when_justified() -> None:
    registry = _registry()
    chat = route(Intent("chat", "hello there"), ContextPackage(), registry)
    assert chat.brain_id == "instinct"
    assert chat.specialist is False
    code = route(Intent("code", "debug this python traceback please"), ContextPackage(), registry)
    assert code.brain_id == "coder"
    assert code.specialist is True
    assert code.bounded is True


def test_routing_learns_from_stored_outcomes() -> None:
    registry = BrainRegistry(
        [
            BrainConfig(id="instinct", role="primary", provider="fake", model="instinct"),
            BrainConfig(
                id="coder-cold",
                role="coding",
                provider="fake",
                model="instinct",
                activation="on_demand",
                capabilities=["code", "debug"],
            ),
            BrainConfig(
                id="coder-hot",
                role="coding",
                provider="fake",
                model="instinct",
                activation="on_demand",
                capabilities=["code", "debug"],
            ),
        ],
        primary_id="instinct",
    )
    package = ContextPackage(
        brain_perf=[
            {"name": "coder-hot", "body": {"brain_id": "coder-hot", "successes": 12, "failures": 0, "latency_ms": 10}},
            {"name": "coder-cold", "body": {"brain_id": "coder-cold", "successes": 1, "failures": 4, "latency_ms": 5}},
        ]
    )
    chat = route(Intent("chat", "help me think"), package, registry)
    assert chat.brain_id == "instinct"
    decision = route(Intent("code", "debug this python traceback please"), package, registry)
    assert decision.brain_id == "coder-hot"
    assert decision.specialist is True
