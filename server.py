#!/usr/bin/env python3
"""Jev-compatible System One endpoint backed by solar-mini4."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from engine import system_one

app = FastAPI(title="solar-mini4-jev", version="0.1")


class SystemOneRequest(BaseModel):
    model: str = Field(default="solar-mini4-jev")
    state: Any
    questions: dict[str, Any]


@app.get("/health")
def health():
    return {"ok": True, "backend": "solar-mini4"}


@app.post("/v1/systemone")
def systemone(body: SystemOneRequest):
    try:
        # allow alias solar-mini4-jev → solar-mini4
        model = "solar-mini4"
        if body.model and body.model not in ("solar-mini4-jev", "solar-mini4", "jev-latest"):
            # still force mini4 backend; record alias in response
            model = "solar-mini4"
        result = system_one(body.state, body.questions, model=model)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {
        "model": result["model"],
        "answers": result["answers"],
        "usage": result["usage"],
        "latency_s": result["latency_s"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8092)
