"""Sleep rewrites durable state so a later session decides differently."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime


def test_sleep_writes_inspectable_dream_and_strategy(cfg: AnimaConfig) -> None:
    being = Runtime(cfg)
    being.boot()
    being.chat("Robert")
    being.chat("my goal is keep the wallet still")
    being.chat("Never spend. Spending cap is 0 wei on Base.")
    report = being.handle("/sleep")
    assert "Dream report" in report.text
    assert being.memory.get_reference("last_dream") is not None
    self_row = being.memory.get_entity("self", "being")
    assert (self_row or {}).get("body", {}).get("sleep_cycles") == 1

    being2 = Runtime(cfg)
    being2.boot()
    being2.new_session()
    reply = being2.chat("what should we do next?")
    assert "goal" in reply.text.lower() or "keep" in reply.text.lower() or "wallet" in reply.text.lower()
    strategies = being2.memory.list_entities("strategy")
    assert strategies, "sleep should have distilled a strategy into Sibyl"
