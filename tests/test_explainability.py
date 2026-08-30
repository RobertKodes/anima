"""/why names memories and brains without dumping hidden chain-of-thought."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime


def test_why_identifies_memories_and_brains(cfg: AnimaConfig) -> None:
    being = Runtime(cfg)
    being.boot()
    being.chat("Robert")
    being.chat("do you remember me?")
    why = being.handle("/why")
    assert "Robert" in why.text or "person" in why.text.lower() or "relationship" in why.text.lower()
    assert "instinct" in why.text.lower() or "brain" in why.text.lower()
    lowered = why.text.lower()
    assert "chain of thought" not in lowered
    assert "private_key" not in lowered
