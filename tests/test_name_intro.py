"""Name introduction and identity recall intents."""

from __future__ import annotations

from anima.config.schema import AnimaConfig
from anima.core.runtime import Runtime, parse_intent


def _fresh(cfg: AnimaConfig) -> Runtime:
    being = Runtime(cfg)
    being.boot()
    return being


def test_intro_phrase_creates_relationship(cfg: AnimaConfig) -> None:
    being = _fresh(cfg)
    being.chat("hello")
    reply = being.chat("hello, i am robert, your maker")
    assert "Robert" in reply.text
    people = being.memory.list_entities("person", limit=10)
    assert any((p.get("body") or {}).get("name") == "Robert" for p in people)


def test_who_am_i_uses_stored_name(cfg: AnimaConfig) -> None:
    being = _fresh(cfg)
    being.chat("hello")
    being.chat("hello, i am robert, your maker")
    reply = being.chat("hello, who am i?")
    assert "Robert" in reply.text
    assert "Anima" not in reply.text or "you" in reply.text.lower()


def test_parse_intent_lowercase_intro() -> None:
    intent = parse_intent("i am robert")
    assert intent.kind == "remember_person"
    assert intent.slots["name"] == "Robert"


def test_parse_intent_who_am_i() -> None:
    assert parse_intent("hello, who am i ?").kind == "ask_memory"
