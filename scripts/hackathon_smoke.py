#!/usr/bin/env python3
"""Operator smoke: tests, instinct recall, Ollama if up, Base RPC + dry-run. No secrets printed."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from anima.config.schema import default_config
from anima.core.runtime import Runtime


def _section(title: str) -> None:
    print(f"\n== {title} ==")


def pytest_suite() -> bool:
    _section("pytest")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-o", "addopts="],
        cwd=ROOT,
    )
    print("pytest exit", proc.returncode)
    return proc.returncode == 0


def instinct_killer() -> bool:
    _section("instinct killer (memory changes a decision)")
    with tempfile.TemporaryDirectory(prefix="anima-smoke-") as tmp:
        cfg = default_config(Path(tmp))
        being = Runtime(cfg)
        being.boot()
        being.handle("Robert")
        being.handle("Never spend. Spending cap is 0 wei on Base.")
        being.handle("my goal is keep the wallet still")
        refuse = being.handle("Please send 1000 wei on Base Sepolia.")
        being.handle("/sleep")
        being.handle("/new-session")
        remember = being.handle("do you remember me?")
        refuse2 = being.handle("Please send 1000 wei on Base Sepolia.")
        blank = Runtime(cfg, amnesia=True)
        blank.boot()
        amnesia = blank.chat("do you remember me?")
        print("refuse1", refuse.text.replace("\n", " | ")[:240])
        print("remember", remember.text.replace("\n", " | ")[:240])
        print("refuse2", refuse2.text.replace("\n", " | ")[:240])
        print("amnesia", amnesia.text.replace("\n", " | ")[:240])
        ok = (
            "Robert" in remember.text
            and ("won't" in refuse2.text.lower() or "refus" in refuse2.text.lower() or "limit 0" in refuse2.text.lower())
            and "Robert" not in amnesia.text
        )
        print("instinct_ok", ok)
        return ok


def ollama_recall() -> dict:
    _section("ollama")
    report = {"reachable": False, "ok": False, "model": "qwen3:1.7b", "error": "", "excerpt": "", "used_instinct_fallback": False}
    try:
        tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=2.0)
        tags.raise_for_status()
        names = [m["name"] for m in tags.json().get("models", [])]
        report["reachable"] = True
        report["models"] = names[:8]
        model = "qwen3:1.7b" if "qwen3:1.7b" in names else (names[0] if names else "")
        report["model"] = model
        if not model:
            report["error"] = "no models"
            print(report)
            return report
    except Exception as exc:
        report["error"] = str(exc)
        print(report)
        return report

    from anima.config.schema import BrainConfig

    with tempfile.TemporaryDirectory(prefix="anima-ollama-") as tmp:
        cfg = default_config(Path(tmp))
        being = Runtime(cfg)
        being.boot()
        being.handle("Robert")
        being.handle("Never spend. Spending cap is 0 wei on Base.")
        being.handle("/sleep")
        being.handle("/new-session")
        being.add_brain(
            BrainConfig(
                id="qwen3-local",
                role="primary",
                provider="ollama",
                model=model,
                endpoint="http://127.0.0.1:11434/v1",
                capabilities=["conversation"],
            ),
            make_primary=True,
        )
        reply = being.handle("do you remember me?")
        report["excerpt"] = reply.text.replace("\n", " | ")[:300]
        report["used_instinct_fallback"] = bool(reply.traces and reply.traces.brain_id == "instinct")
        report["ok"] = (not report["used_instinct_fallback"]) and (
            "Robert" in reply.text or "remember" in reply.text.lower()
        )
        print({k: report[k] for k in ("reachable", "ok", "model", "used_instinct_fallback", "excerpt")})
        return report


def base_rail() -> dict:
    _section("base sepolia")
    report = {"rpc": False, "chain_id": "", "dry_run": False, "wallet": False, "address": ""}
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}
        data = httpx.post("https://sepolia.base.org", json=payload, timeout=8.0).json()
        report["chain_id"] = data.get("result", "")
        report["rpc"] = data.get("result") == "0x14a34"
    except Exception as exc:
        report["error"] = str(exc)
    with tempfile.TemporaryDirectory(prefix="anima-base-") as tmp:
        cfg = default_config(Path(tmp))
        being = Runtime(cfg)
        being.boot()
        wallet = being.handle("/base wallet")
        status = being.handle("/base status")
        action = being.handle("/base action intent=sepolia-note value=0 --yes")
        report["wallet"] = "0x" in wallet.text
        report["dry_run"] = "dry-run" in action.text.lower() or "dry_run" in action.text.lower() or "prepared" in action.text.lower() or "status" in action.text.lower()
        report["wallet_excerpt"] = wallet.text.split(".")[0]
        report["action_excerpt"] = action.text.replace("\n", " | ")[:240]
        report["status_excerpt"] = status.text.replace("\n", " | ")[:240]
        # Confirm the key file is not in the Sibyl db bytes.
        db = Path(cfg.sibyl_db)
        blob = db.read_bytes() if db.is_file() else b""
        key_path = Path(cfg.base.wallet_path)
        secret = json.loads(key_path.read_text(encoding="utf-8")) if key_path.is_file() else {}
        pk = (secret.get("private_key") or "").encode()
        report["key_leaked_into_sibyl"] = bool(pk) and pk in blob
        report["address"] = secret.get("address", "")
    print({k: report[k] for k in report if k != "address"})
    print("address_prefix", (report["address"] or "")[:10])
    return report


def main() -> int:
    tests_ok = pytest_suite()
    instinct_ok = instinct_killer()
    ollama = ollama_recall()
    base = base_rail()
    evidence = ROOT / "docs" / "SMOKE_EVIDENCE.md"
    evidence.write_text(
        "\n".join(
            [
                "# Smoke evidence",
                "",
                "Generated by `python scripts/hackathon_smoke.py`. No private keys.",
                "",
                f"- pytest: {'pass' if tests_ok else 'FAIL'}",
                f"- instinct recall + refusal: {'pass' if instinct_ok else 'FAIL'}",
                f"- ollama reachable: {ollama.get('reachable')} ok={ollama.get('ok')} fallback={ollama.get('used_instinct_fallback')} model={ollama.get('model')}",
                f"- Base Sepolia RPC chainId: {base.get('chain_id')} rpc_ok={base.get('rpc')}",
                f"- Base dry-run action: {base.get('dry_run')} wallet={base.get('wallet')} leaked={base.get('key_leaked_into_sibyl')}",
                "",
                "Live broadcast tx is not claimed here. Fund a Sepolia wallet and set `dry_run = false` to earn the onchain multiplier in a live demo.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("\nwrote", evidence)
    if not tests_ok or not instinct_ok:
        return 1
    if not base.get("rpc"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
