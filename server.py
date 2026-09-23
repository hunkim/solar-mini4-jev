#!/usr/bin/env python3
"""Jev-compatible System One endpoint backed by solar-mini4 (BYOK)."""
from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from engine import system_one

app = FastAPI(
    title="solar-mini4-jev",
    version="0.2",
    description=(
        "Drop-in System One API for Solar Mini4. "
        "BYOK: pass your Upstage key per request via "
        "`X-Upstage-Api-Key` or `Authorization: Bearer <key>`."
    ),
    docs_url="/api-docs",
    redoc_url="/api-redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Flexible JSON values matching TypeSafe OpenAPI anyOf for instructions/descriptions.
FlexibleText = Annotated[
    Union[str, dict[str, Any], list[Any], None],
    Field(description="string | object | array | null (Jev-compatible)"),
]


class NoulCriteria(BaseModel):
    """Criteria defining what counts as yes/no. true/false may be nested."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    true: FlexibleText = None
    false: FlexibleText = None


class NoulQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["noul"]
    instructions: FlexibleText = None
    criteria: NoulCriteria | None = None


# Score level descriptions: string | object | array (null not in TypeSafe items anyOf).
ScoreLevel = Annotated[
    Union[str, dict[str, Any], list[Any]],
    Field(description="string | object | array (Jev score criteria item)"),
]


class ChoiceQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["choice"]
    instructions: FlexibleText = None
    # Values mirror TypeSafe: string | object | array | null
    criteria: dict[str, FlexibleText]


class ScoreQuestion(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["score"]
    instructions: FlexibleText = None
    criteria: list[ScoreLevel] = Field(min_length=1)


Question = Annotated[
    Union[NoulQuestion, ChoiceQuestion, ScoreQuestion],
    Field(discriminator="type"),
]


class SystemOneRequest(BaseModel):
    """Request shape aligned with TypeSafe SystemOneRequest."""

    model: str = Field(default="solar-mini4-jev")
    state: Any
    questions: dict[str, Question] = Field(min_length=1)


def _extract_byok(
    authorization: str | None,
    x_upstage_api_key: str | None,
    x_api_key: str | None,
) -> str:
    if x_upstage_api_key and x_upstage_api_key.strip():
        return x_upstage_api_key.strip()
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization:
        raw = authorization.strip()
        if raw.lower().startswith("bearer "):
            token = raw[7:].strip()
            if token:
                return token
        elif raw:
            return raw
    raise HTTPException(
        status_code=401,
        detail={
            "error": "missing_api_key",
            "message": (
                "BYOK required. Send your Upstage API key as "
                "`X-Upstage-Api-Key: <key>` or `Authorization: Bearer <key>`."
            ),
        },
    )


def _questions_as_dicts(body: SystemOneRequest) -> dict[str, Any]:
    """Pass validated questions to the engine as plain dicts."""
    out: dict[str, Any] = {}
    for name, q in body.questions.items():
        out[name] = q.model_dump(by_alias=True, exclude_none=False)
    return out


@app.get("/")
def root():
    return {
        "service": "solar-mini4-jev",
        "byok": True,
        "endpoints": {
            "health": "GET /health",
            "systemone": "POST /v1/systemone",
        },
        "auth": ["X-Upstage-Api-Key", "Authorization: Bearer <UPSTAGE_API_KEY>"],
    }


@app.get("/health")
def health():
    return {"ok": True, "backend": "solar-mini4", "byok": True}


@app.post("/v1/systemone")
def systemone(
    body: SystemOneRequest,
    authorization: str | None = Header(default=None),
    x_upstage_api_key: str | None = Header(default=None, alias="X-Upstage-Api-Key"),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    api_key = _extract_byok(authorization, x_upstage_api_key, x_api_key)
    try:
        model = "solar-mini4"
        if body.model and body.model not in ("solar-mini4-jev", "solar-mini4", "jev-latest"):
            model = "solar-mini4"
        result = system_one(
            body.state,
            _questions_as_dicts(body),
            model=model,
            api_key=api_key,
        )
    except RuntimeError as e:
        # missing key / bad config
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {
        "model": result["model"],
        "answers": result["answers"],
        "usage": result["usage"],
        "latency_s": result["latency_s"],
    }


# Alias used by some Jev clients
@app.post("/v1/systemone/")
def systemone_slash(
    body: SystemOneRequest,
    authorization: str | None = Header(default=None),
    x_upstage_api_key: str | None = Header(default=None, alias="X-Upstage-Api-Key"),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    return systemone(body, authorization, x_upstage_api_key, x_api_key)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8092)
