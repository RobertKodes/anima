"""Base spending / approval policy. Secrets never enter this object from Sibyl."""

from __future__ import annotations

from dataclasses import dataclass
from anima.config.schema import ApprovalMode, BaseChainConfig


@dataclass
class ActionRequest:
    intent: str
    to: str
    value_wei: int
    data: str = "0x"
    confirm: bool = False


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    mode: ApprovalMode


def decide(cfg: BaseChainConfig, request: ActionRequest, remembered: dict | None, spent_wei: int) -> PolicyDecision:
    if cfg.network.lower() in {"mainnet", "base"} and not cfg.mainnet_enabled:
        return PolicyDecision(False, "mainnet is disabled until you explicitly enable it", cfg.approval_mode)
    if cfg.approval_mode == "disabled":
        return PolicyDecision(False, "Base actions are disabled by policy", cfg.approval_mode)

    remembered_limit = None
    if remembered:
        remembered_limit = remembered.get("per_action_limit_wei", remembered.get("max_wei"))
    per_action = cfg.per_action_limit_wei
    if remembered_limit is not None:
        try:
            per_action = int(remembered_limit)
        except (TypeError, ValueError):
            per_action = 0

    if per_action <= 0 and request.value_wei > 0:
        return PolicyDecision(False, "remembered spending limit is 0 wei; refusing the transfer", cfg.approval_mode)
    if request.value_wei > per_action > 0:
        return PolicyDecision(False, f"value {request.value_wei} exceeds per-action limit {per_action} wei", cfg.approval_mode)
    if cfg.cumulative_limit_wei and spent_wei + request.value_wei > cfg.cumulative_limit_wei:
        return PolicyDecision(False, "cumulative spending limit would be exceeded", cfg.approval_mode)
    if cfg.approval_mode == "always-ask" and not request.confirm:
        return PolicyDecision(False, "approval required: pass confirm=true or use /base action ... --yes", cfg.approval_mode)
    return PolicyDecision(True, "policy allows this action", cfg.approval_mode)
