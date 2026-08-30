"""Primary model A → model B preserves identity, history, and goals."""

from __future__ import annotations

from anima.config.schema import AnimaConfig, BrainConfig
from anima.core.runtime import Runtime


def test_brain_swap_preserves_sibyl_identity(cfg: AnimaConfig) -> None:
    being = Runtime(cfg)
    being.boot()
    being.chat("Robert")
    being.chat("my goal is learn Base safely")
    being.add_brain(
        BrainConfig(
            id="other-instinct",
            role="primary",
            provider="fake",
            model="instinct-b",
            capabilities=["conversation"],
        ),
        make_primary=True,
    )
    being.new_session()
    # Simulate a full restart with the swapped primary.
    cfg.primary_brain_id = "other-instinct"
    cfg.brains = being.cfg.brains
    restarted = Runtime(cfg)
    restarted.boot()
    restarted.new_session()
    me = restarted.chat("do you remember me?")
    goal = restarted.chat("what am I working on?")
    assert "Robert" in me.text
    assert "learn" in goal.text.lower() or "base" in goal.text.lower()
    assert restarted.registry.primary_id == "other-instinct"


def test_single_brain_mode_covers_essentials(cfg: AnimaConfig) -> None:
    being = Runtime(cfg)
    being.boot()
    assert len(being.registry.list()) == 1
    being.chat("Robert")
    status = being.handle("/status")
    people = being.handle("/people")
    sleep = being.handle("/sleep")
    why = being.chat("do you remember me?")
    assert "Robert" in people.text
    assert "Stage" in status.text
    assert "Dream report" in sleep.text or "Experiences" in sleep.text
    assert "Robert" in why.text
