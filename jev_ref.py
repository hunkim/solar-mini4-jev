"""Thin real TypeSafe Jev client for benchmarking."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"


def system_one(state: Any, questions: dict[str, Any], *, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    key = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not set")
    body = json.dumps({"model": model, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Jev HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from e
    latency_s = time.perf_counter() - t0
    return {
        "model": raw.get("model") or model,
        "answers": raw.get("answers") or {},
        "usage": raw.get("usage") or {},
        "latency_s": round(latency_s, 4),
        "raw": raw,
    }
