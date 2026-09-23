"""TypeSafe Jev System One request-shape helpers (mirrors official OpenAPI).

Official NoulCriteria.true/false accept: string | object | array | null.
instructions accept: string | object | array | null.
choice criteria values and score criteria items accept the same nested shapes.
"""
from __future__ import annotations

import json
from typing import Any


def instructions_text(instructions: Any) -> str:
    """Flatten Jev-flexible instructions into a single string for prompts/heuristics."""
    if instructions is None:
        return ""
    if isinstance(instructions, str):
        return instructions.strip()
    if isinstance(instructions, list):
        parts = [instructions_text(x) for x in instructions]
        return " ".join(p for p in parts if p).strip()
    if isinstance(instructions, dict):
        # Prefer common human keys when present; else stable JSON.
        for key in ("question", "task", "text", "prompt", "instruction"):
            if key in instructions and instructions[key] is not None:
                rest = {k: v for k, v in instructions.items() if k != key}
                head = instructions_text(instructions[key])
                if rest:
                    return f"{head} {json.dumps(rest, ensure_ascii=False)}".strip()
                return head
        return json.dumps(instructions, ensure_ascii=False)
    return str(instructions).strip()


def description_text(value: Any) -> str:
    """Render a criteria description (string | object | array | null) for prompts."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def legend_value(value: Any) -> Any:
    """Pass nested score criteria through to answer legend (Jev keeps structure)."""
    return value
