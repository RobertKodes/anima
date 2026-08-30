"""Wallet kept off the memory substrate. Address may be remembered; keys may not."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eth_account import Account
from web3 import Web3

from anima.base.policy import ActionRequest, decide
from anima.config.schema import BaseChainConfig


@dataclass
class PreparedAction:
    intent: str
    to: str
    value_wei: int
    nonce: int | None
    chain_id: int
    from_address: str
    dry_run: bool


class BaseAdapter:
    def __init__(self, cfg: BaseChainConfig) -> None:
        self.cfg = cfg
        self.wallet_path = Path(cfg.wallet_path).expanduser() if cfg.wallet_path else None
        self._w3: Web3 | None = None

    def status(self) -> dict[str, Any]:
        address = self.address()
        return {
            "network": self.cfg.network,
            "chain_id": self.cfg.chain_id,
            "rpc": self.cfg.rpc,
            "approval_mode": self.cfg.approval_mode,
            "mainnet_enabled": self.cfg.mainnet_enabled,
            "dry_run": self.cfg.dry_run,
            "address": address,
            "wallet_file": str(self.wallet_path) if self.wallet_path else None,
            "reachable": self._reachable(),
        }

    def address(self) -> str | None:
        if not self.wallet_path or not self.wallet_path.is_file():
            return None
        data = json.loads(self.wallet_path.read_text(encoding="utf-8"))
        return data.get("address")

    def ensure_wallet(self) -> str:
        if not self.wallet_path:
            raise RuntimeError("no wallet_path configured")
        self.wallet_path.parent.mkdir(parents=True, exist_ok=True)
        if self.wallet_path.is_file():
            address = self.address()
            if address:
                return address
        account = Account.create()
        payload = {"address": account.address, "private_key": account.key.hex()}
        self.wallet_path.write_text(json.dumps(payload), encoding="utf-8")
        os.chmod(self.wallet_path, 0o600)
        return account.address

    def prepare(self, request: ActionRequest) -> PreparedAction:
        address = self.address() or "0x0000000000000000000000000000000000000000"
        nonce = None
        if not self.cfg.dry_run:
            w3 = self._web3()
            if w3 is not None and address.startswith("0x") and address != "0x0000000000000000000000000000000000000000":
                nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(address))
        return PreparedAction(
            intent=request.intent,
            to=request.to,
            value_wei=request.value_wei,
            nonce=nonce,
            chain_id=self.cfg.chain_id,
            from_address=address,
            dry_run=self.cfg.dry_run,
        )

    def execute(self, request: ActionRequest, remembered_policy: dict | None, spent_wei: int) -> dict[str, Any]:
        decision = decide(self.cfg, request, remembered_policy, spent_wei)
        prepared = self.prepare(request)
        record = {
            "intent": request.intent,
            "to": request.to,
            "value_wei": request.value_wei,
            "from": prepared.from_address,
            "chain_id": prepared.chain_id,
            "network": self.cfg.network,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "dry_run": self.cfg.dry_run,
            "status": "refused" if not decision.allowed else "prepared",
        }
        if not decision.allowed:
            return record
        if self.cfg.dry_run:
            record["tx_id"] = "dry-run-" + request.intent.replace(" ", "-")[:24]
            record["status"] = "dry-run"
            return record
        tx_id = self._broadcast(request, prepared)
        record["tx_id"] = tx_id
        record["status"] = "submitted"
        return record

    def _broadcast(self, request: ActionRequest, prepared: PreparedAction) -> str:
        if not self.wallet_path or not self.wallet_path.is_file():
            raise RuntimeError("wallet file missing")
        secret = json.loads(self.wallet_path.read_text(encoding="utf-8"))
        key = secret.get("private_key")
        if not key:
            raise RuntimeError("wallet has no private_key")
        w3 = self._web3()
        if w3 is None:
            raise RuntimeError("cannot reach Base RPC")
        checksum_from = Web3.to_checksum_address(prepared.from_address)
        tx = {
            "chainId": self.cfg.chain_id,
            "from": checksum_from,
            "to": Web3.to_checksum_address(request.to),
            "value": int(request.value_wei),
            "nonce": prepared.nonce or w3.eth.get_transaction_count(checksum_from),
            "gas": 21000,
            "maxFeePerGas": w3.to_wei("0.1", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("0.1", "gwei"),
            "data": request.data or "0x",
        }
        signed = w3.eth.account.sign_transaction(tx, private_key=key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def _web3(self) -> Web3 | None:
        if self._w3 is None:
            self._w3 = Web3(Web3.HTTPProvider(self.cfg.rpc, request_kwargs={"timeout": 20}))
        return self._w3

    def _reachable(self) -> bool:
        if self.cfg.dry_run:
            return True
        try:
            w3 = self._web3()
            return bool(w3 and w3.is_connected())
        except Exception:
            return False
