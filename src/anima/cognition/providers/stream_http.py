"""Shared streaming helpers for HTTP brains."""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from anima.cognition.providers.base import StreamChunk


def iter_sse_token_deltas(response: httpx.Response) -> Iterator[StreamChunk]:
    for line in response.iter_lines():
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for choice in data.get("choices") or []:
            delta = choice.get("delta") or {}
            reasoning = delta.get("reasoning_content") or delta.get("reasoning") or ""
            if reasoning:
                yield StreamChunk("think", reasoning)
            content = delta.get("content") or ""
            if content:
                yield StreamChunk("token", content)
