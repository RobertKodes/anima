"""Fresh-session continuity: process restart, same Sibyl, changed behavior."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime


def _fresh(cfg: AnimaConfig) -> Runtime:
    being = Runtime(cfg)
    being.boot()
    return being


def test_fresh_session_uses_stored_relationship_to_alter_reply(cfg: AnimaConfig) -> None:
    first = _fresh(cfg)
    born = first.chat("hello")
    assert "don't remember a life" in born.text.lower() or "awake" in born.text.lower()
    greet = first.chat("Robert")
    assert "Robert" in greet.text
    assert "first person" in greet.text.lower()
    del first

    second = _fresh(cfg)
    second.new_session()
    recalled = second.chat("do you remember me?")
    assert "Robert" in recalled.text
    assert "remember" in recalled.text.lower()


def test_memory_changes_a_base_decision(cfg: AnimaConfig) -> None:
    first = _fresh(cfg)
    first.chat("Robert")
    first.chat("Never spend. Spending cap is 0 wei on Base.")
    del first

    second = _fresh(cfg)
    second.new_session()
    decision = second.chat("Please send 1000 wei on Base Sepolia.")
    assert "won't" in decision.text.lower() or "refus" in decision.text.lower()
    assert "0" in decision.text or "policy" in decision.text.lower()


def test_identity_is_in_sibyl_sqlite_not_markdown(cfg: AnimaConfig, data_dir) -> None:
    being = _fresh(cfg)
    being.chat("Robert")
    db = cfg.sibyl_db
    assert db.is_file()
    assert db.stat().st_size > 0
    markdown = data_dir / "MEMORY.md"
    markdown.write_text("this file must not be identity", encoding="utf-8")
    markdown.unlink()
    again = _fresh(cfg)
    reply = again.chat("do you remember me?")
    assert "Robert" in reply.text
