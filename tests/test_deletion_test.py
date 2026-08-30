"""Deleting or isolating Sibyl must materially break the developed being."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime


def test_amnesia_mode_cannot_use_stored_identity(cfg: AnimaConfig) -> None:
    taught = Runtime(cfg)
    taught.boot()
    taught.chat("Robert")
    taught.chat("Never spend. Spending cap is 0 wei on Base.")
    taught.chat("my goal is keep the wallet still")

    blank = Runtime(cfg, amnesia=True)
    boot = blank.boot()
    assert boot.birth
    recalled = blank.chat("do you remember me?")
    assert "Robert" not in recalled.text
    spend = blank.chat("Please send 1000 wei on Base Sepolia.")
    assert "won't" not in spend.text.lower()
    assert "Robert" not in spend.text
    # Real store still exists and still holds the life.
    alive = Runtime(cfg)
    alive.boot()
    proof = alive.chat("do you remember me?")
    assert "Robert" in proof.text


def test_missing_sibyl_file_is_a_newborn_not_the_same_being(cfg: AnimaConfig, tmp_path) -> None:
    being = Runtime(cfg)
    being.boot()
    being.chat("Robert")
    other_cfg = cfg.model_copy(update={"sibyl_db": tmp_path / "empty" / "memory.db"})
    other = Runtime(other_cfg)
    other.boot()
    reply = other.chat("do you remember me?")
    assert "Robert" not in reply.text
