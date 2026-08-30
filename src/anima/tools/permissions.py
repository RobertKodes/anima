"""Permission checks for risky capabilities."""

from __future__ import annotations

from anima.tools.registry import CapabilityRegistry


def may(registry: CapabilityRegistry, cap_id: str) -> tuple[bool, str]:
    for item in registry.items:
        if item.id == cap_id:
            if item.granted:
                return True, "granted"
            return False, f"{item.title} is not granted"
    return False, f"unknown capability {cap_id}"
