"""Development metrics derived from real Sibyl state. Not cosmetic XP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from anima.memory.sibyl_adapter import (
    CAT_CAPABILITY,
    CAT_GOAL,
    CAT_ONCHAIN,
    CAT_PERSON,
    CAT_STRATEGY,
    CAT_SELF,
    SELF_NAME,
    DisabledMemory,
    SibylAdapter,
)

Memory = SibylAdapter | DisabledMemory

STAGES = ("Newborn", "Learner", "Developing", "Independent")


@dataclass
class DevelopmentSnapshot:
    stage: str
    evidence: dict[str, Any]
    age_turns: int
    sleep_cycles: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "age_turns": self.age_turns,
            "sleep_cycles": self.sleep_cycles,
            "evidence": self.evidence,
        }


def snapshot(memory: Memory) -> DevelopmentSnapshot:
    if not memory.enabled:
        return DevelopmentSnapshot("Newborn", {"amnesia": True}, 0, 0)
    self_row = memory.get_entity(CAT_SELF, SELF_NAME)
    self_body = (self_row or {}).get("body") or {}
    people = memory.list_entities(CAT_PERSON, limit=50)
    goals = memory.list_entities(CAT_GOAL, limit=50)
    strategies = memory.list_entities(CAT_STRATEGY, limit=50)
    caps = memory.list_entities(CAT_CAPABILITY, limit=50)
    chain = memory.list_entities(CAT_ONCHAIN, limit=50)
    events = memory.read_events(limit=200)
    session = memory.get_state("session") or {}
    sleep_cycles = int(self_body.get("sleep_cycles") or 0)
    completed_goals = [g for g in goals if (g.get("body") or {}).get("status") == "done"]
    evidence = {
        "relationships": len(people),
        "experiences": len(events),
        "goals": len(goals),
        "completed_goals": len(completed_goals),
        "strategies": len(strategies),
        "capabilities_logged": len(caps),
        "onchain_actions": len(chain),
        "sleep_cycles": sleep_cycles,
        "memory_enabled": True,
    }
    stage = "Newborn"
    if evidence["relationships"] >= 1 and evidence["experiences"] >= 3:
        stage = "Learner"
    if stage == "Learner" and evidence["goals"] >= 1 and evidence["sleep_cycles"] >= 1 and evidence["strategies"] >= 1:
        stage = "Developing"
    if (
        stage == "Developing"
        and evidence["capabilities_logged"] >= 1
        and evidence["onchain_actions"] >= 1
        and evidence["sleep_cycles"] >= 2
    ):
        stage = "Independent"
    return DevelopmentSnapshot(stage, evidence, int(session.get("turns") or len(events)), sleep_cycles)
