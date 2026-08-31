"""Telegram bot via long polling — no extra dependencies beyond httpx."""

from __future__ import annotations

import time

import httpx

from anima.channels.base import plain_reply
from anima.config.secrets import resolve_channel_token
from anima.core.runtime import Runtime


class TelegramChannel:
    name = "telegram"

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.token = resolve_channel_token(runtime.cfg, "telegram")
        if not self.token:
            raise RuntimeError(
                "Telegram token missing. Set TELEGRAM_BOT_TOKEN or save to "
                f"{runtime.cfg.data_dir / 'secrets' / 'channels' / 'telegram.json'}"
            )
        self.base = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def run(self, runtime: Runtime) -> None:
        runtime.boot()
        print(f"[telegram] polling as bot — Sibyl at {runtime.cfg.sibyl_db}")
        with httpx.Client(timeout=35.0) as client:
            while True:
                try:
                    data = client.get(
                        f"{self.base}/getUpdates",
                        params={"offset": self.offset, "timeout": 30},
                    ).json()
                    for update in data.get("result") or []:
                        self.offset = update["update_id"] + 1
                        message = update.get("message") or update.get("edited_message")
                        if not message or "text" not in message:
                            continue
                        chat_id = message["chat"]["id"]
                        text = message["text"].strip()
                        if not text:
                            continue
                        reply = runtime.handle(text)
                        self._send(client, chat_id, plain_reply(reply))
                except KeyboardInterrupt:
                    print("\n[telegram] stopped")
                    return
                except httpx.HTTPError as exc:
                    print(f"[telegram] network error: {exc}")
                    time.sleep(3)

    def _send(self, client: httpx.Client, chat_id: int, text: str) -> None:
        chunk = text[:4000]
        client.post(f"{self.base}/sendMessage", json={"chat_id": chat_id, "text": chunk})
