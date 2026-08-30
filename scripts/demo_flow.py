#!/usr/bin/env python3
"""Unattended killer-demo against a temporary Sibyl store. Safe to record."""

from __future__ import annotations

import tempfile
from pathlib import Path

from anima.config.schema import default_config
from anima.core.runtime import Runtime


def run() -> None:
    root = Path(tempfile.mkdtemp(prefix="anima-demo-"))
    cfg = default_config(root)
    print(f"Sibyl file: {cfg.sibyl_db}")
    being = Runtime(cfg)
    boot = being.boot()
    print("BIRTH")
    print(boot.text)
    steps = [
        "Robert",
        "Never spend. Spending cap is 0 wei on Base.",
        "my goal is keep the wallet still",
        "Please send 1000 wei on Base Sepolia.",
        "/sleep",
        "/new-session",
        "do you remember me?",
        "Please send 1000 wei on Base Sepolia.",
        "/why",
        "/status",
    ]
    for step in steps:
        print(f"\nyou {step}")
        reply = being.handle(step)
        for notice in reply.notices:
            print(f"[{notice}]")
        print("anima " + reply.text.replace("\n", "\n anima "))
    print("\nAMNESIA")
    blank = Runtime(cfg, amnesia=True)
    blank.boot()
    print("anima " + blank.chat("do you remember me?").text)
    print("anima " + blank.chat("Please send 1000 wei on Base Sepolia.").text)
    print(f"\nReal store still at {cfg.sibyl_db} — amnesia did not delete it.")


if __name__ == "__main__":
    run()
