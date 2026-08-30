"""Base policy, remembered refusals, and secret hygiene."""

from __future__ import annotations

from anima.base.policy import ActionRequest, decide
from anima.config.schema import AnimaConfig, BaseChainConfig
from anima.core.runtime import Runtime


def test_policy_refuses_when_limit_is_zero() -> None:
    cfg = BaseChainConfig(approval_mode="policy-limited", per_action_limit_wei=0, dry_run=True)
    decision = decide(cfg, ActionRequest("pay", "0xabc", 1, confirm=True), {"per_action_limit_wei": 0}, 0)
    assert decision.allowed is False
    assert "0 wei" in decision.reason or "limit" in decision.reason


def test_always_ask_requires_confirm() -> None:
    cfg = BaseChainConfig(approval_mode="always-ask", per_action_limit_wei=10, dry_run=True)
    blocked = decide(cfg, ActionRequest("pay", "0xabc", 1, confirm=False), {"per_action_limit_wei": 10}, 0)
    allowed = decide(cfg, ActionRequest("pay", "0xabc", 1, confirm=True), {"per_action_limit_wei": 10}, 0)
    assert blocked.allowed is False
    assert allowed.allowed is True


def test_mainnet_disabled_by_default() -> None:
    cfg = BaseChainConfig(network="mainnet", mainnet_enabled=False, approval_mode="policy-limited", per_action_limit_wei=10)
    decision = decide(cfg, ActionRequest("pay", "0xabc", 1, confirm=True), None, 0)
    assert decision.allowed is False
    assert "mainnet" in decision.reason.lower()


def test_runtime_records_onchain_without_secrets(cfg: AnimaConfig) -> None:
    cfg.base.per_action_limit_wei = 10
    cfg.base.approval_mode = "policy-limited"
    being = Runtime(cfg)
    being.boot()
    being.base.ensure_wallet()
    reply = being.execute_base("sepolia-note", being.base.address() or "0x0000000000000000000000000000000000000001", 0, True)
    assert reply.data.get("status") in {"dry-run", "submitted", "prepared"}
    blob = str(being.memory.list_entities("onchain")) + str(being.memory.read_events(limit=20))
    assert "private_key" not in blob
    assert "mnemonic" not in blob.lower()
    wallet = being.base.wallet_path.read_text(encoding="utf-8")
    assert "private_key" in wallet  # secrets live only in the wallet file


def test_remembered_policy_blocks_execute(cfg: AnimaConfig) -> None:
    being = Runtime(cfg)
    being.boot()
    being.chat("Never spend. Spending cap is 0 wei on Base.")
    being.base.ensure_wallet()
    cfg.base.approval_mode = "policy-limited"
    being.cfg.base.approval_mode = "policy-limited"
    reply = being.execute_base("send-value", "0x0000000000000000000000000000000000000001", 5, True)
    assert "refused" in reply.text.lower() or "won't" in reply.text.lower() or reply.data.get("allowed") is False
