"""Wallet kept off the memory substrate. Address may be remembered; keys may not."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anima.base.policy import ActionRequest, decide
from anima.config.schema import BaseChainConfig

if TYPE_CHECKING:
    from web3 import Web3 as Web3Type


_BASE_IMPORT_ERROR: str | None = None


def base_crypto_available() -> tuple[bool, str]:
    """Whether eth-account can be imported for live signing (ckzg may block on Windows)."""
    global _BASE_IMPORT_ERROR
    if _BASE_IMPORT_ERROR is not None:
        return False, _BASE_IMPORT_ERROR
    try:
        import eth_account  # noqa: F401
    except ImportError as exc:
        _BASE_IMPORT_ERROR = str(exc)
        return False, str(exc)
    return True, ""


def wallet_creation_available() -> tuple[bool, str]:
    """Whether a local wallet file can be created (eth_keys works even when ckzg is blocked)."""
    try:
        import eth_keys  # noqa: F401
    except ImportError as exc:
        return False, str(exc)
    return True, ""


def _create_wallet_keypair() -> tuple[str, str]:
    ok, reason = base_crypto_available()
    if ok:
        from eth_account import Account

        account = Account.create()
        return account.address, account.key.hex()
    ok, reason = wallet_creation_available()
    if not ok:
        raise RuntimeError(f"cannot create a wallet on this machine ({reason})")
    import os

    from eth_keys import keys

    private_key = keys.PrivateKey(os.urandom(32))
    return private_key.public_key.to_checksum_address(), private_key.to_hex()


def _require_account():
    ok, reason = base_crypto_available()
    if not ok:
        raise RuntimeError(
            "Base wallet signing is unavailable on this machine "
            f"({reason}). Dry-run and policy checks still work; "
            "install eth-account or allow ckzg to create wallets or broadcast."
        )
    from eth_account import Account

    return Account


def _require_web3() -> type[Web3Type]:
    ok, reason = base_crypto_available()
    if not ok:
        raise RuntimeError(f"web3 is unavailable on this machine ({reason})")
    from web3 import Web3

    return Web3


def _secure_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except (OSError, NotImplementedError):
        pass


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
        self._w3: Web3Type | None = None

    def status(self) -> dict[str, Any]:
        crypto_ok, crypto_reason = base_crypto_available()
        wallet_ok, wallet_reason = wallet_creation_available()
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
            "crypto_available": crypto_ok,
            "crypto_error": crypto_reason or None,
            "wallet_available": wallet_ok,
            "wallet_error": wallet_reason or None,
        }

    def address(self) -> str | None:
        if not self.wallet_path or not self.wallet_path.is_file():
            return None
        data = self._read_wallet()
        return data.get("address")

    def ensure_wallet(self) -> str:
        if not self.wallet_path:
            raise RuntimeError("no wallet_path configured")
        self.wallet_path.parent.mkdir(parents=True, exist_ok=True)
        if self.wallet_path.is_file():
            data = self._read_wallet()
            address = data.get("address")
            if address:
                return str(address)
            if data.get("private_key"):
                raise RuntimeError(
                    f"wallet file {self.wallet_path} has a private key but no address; "
                    "refusing to overwrite — fix the file manually"
                )
            raise RuntimeError(
                f"wallet file {self.wallet_path} exists but has no address; "
                "refusing to overwrite a possibly corrupt wallet"
            )
        address, private_key = _create_wallet_keypair()
        payload = {"address": address, "private_key": private_key}
        self.wallet_path.write_text(json.dumps(payload), encoding="utf-8")
        _secure_file(self.wallet_path)
        return address

    def prepare(self, request: ActionRequest) -> PreparedAction:
        address = self.address() or "0x0000000000000000000000000000000000000000"
        nonce = None
        if not self.cfg.dry_run:
            w3 = self._web3()
            Web3 = _require_web3()
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

    def _read_wallet(self) -> dict[str, Any]:
        if not self.wallet_path:
            return {}
        try:
            data = json.loads(self.wallet_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"wallet file is corrupt: {self.wallet_path}") from exc
        return data if isinstance(data, dict) else {}

    def _broadcast(self, request: ActionRequest, prepared: PreparedAction) -> str:
        if not self.wallet_path or not self.wallet_path.is_file():
            raise RuntimeError("wallet file missing")
        secret = self._read_wallet()
        key = secret.get("private_key")
        if not key:
            raise RuntimeError("wallet has no private_key")
        w3 = self._web3()
        if w3 is None:
            raise RuntimeError("cannot reach Base RPC")
        Web3 = _require_web3()
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

    def _web3(self) -> Web3Type | None:
        if self._w3 is None:
            Web3 = _require_web3()
            self._w3 = Web3(Web3.HTTPProvider(self.cfg.rpc, request_kwargs={"timeout": 20}))
        return self._w3

    def _reachable(self) -> bool:
        if self.cfg.dry_run:
            return True
        if not base_crypto_available()[0]:
            return False
        try:
            w3 = self._web3()
            return bool(w3 and w3.is_connected())
        except Exception:
            return False
