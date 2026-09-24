# solar-mini4-jev

A drop-in wrapper that exposes Upstage **Solar Pro4** (default; `solar-mini4` optional) through the TypeSafe Jev System One API shape.

```
POST /v1/systemone
{ "model": "solar-mini4-jev", "state": "...", "questions": { ... } }
```

Supported question types: `noul` | `choice` | `score` (same schema as Jev).

## Try the live API (Vercel)

Hosted BYOK endpoint — no deploy needed to try it:

- API: https://solar-mini4-jev.vercel.app
- Health: https://solar-mini4-jev.vercel.app/health
- Docs / examples: https://hunkim.github.io/solar-mini4-jev/
- LLM reference: https://hunkim.github.io/solar-mini4-jev/llms.txt

```bash
curl -s https://solar-mini4-jev.vercel.app/v1/systemone \
  -H "Content-Type: application/json" \
  -H "X-Upstage-Api-Key: $UPSTAGE_API_KEY" \
  -d '{
    "model": "solar-mini4-jev",
    "state": "Payment success rate dropped to 12%.",
    "questions": {
      "urgent": {"type": "noul", "instructions": "Should on-call be paged immediately?"}
    }
  }'
```

Bring your own [Upstage API key](https://console.upstage.ai/api-keys). The server does not store it.

## For LLMs

Machine-readable API reference: [`llms.txt`](https://hunkim.github.io/solar-mini4-jev/llms.txt)

Docs: https://hunkim.github.io/solar-mini4-jev/

## Deploy (Vercel) · BYOK System One

The live API is **Bring Your Own Key**. The server never stores your Upstage key.

```bash
# local
uvicorn server:app --host 0.0.0.0 --port 8092

# call (System One shape)
curl -s https://solar-mini4-jev.vercel.app/v1/systemone \
  -H "Content-Type: application/json" \
  -H "X-Upstage-Api-Key: $UPSTAGE_API_KEY" \
  -d '{
    "model": "solar-mini4-jev",
    "state": "Payment success rate dropped to 12%.",
    "questions": {
      "urgent": {"type": "noul", "instructions": "Should on-call be paged immediately?"}
    }
  }'
```

Auth headers (any one):
- `X-Upstage-Api-Key: <upstage_key>`
- `Authorization: Bearer <upstage_key>`

Deploy:

```bash
npx vercel@latest --prod
```

Routes:
- `GET /` — scorecard (static)
- `GET /health` — liveness
- `POST /v1/systemone` — System One API (BYOK)

No `UPSTAGE_API_KEY` is required in Vercel project env for production BYOK. Optional env only for local/dev convenience.

## Quick start

```bash
export UPSTAGE_API_KEY=...
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

```python
from engine import system_one

out = system_one(
    state="Payment success rate dropped to 12%.",
    questions={"urgent": {"type": "noul", "instructions": "Should on-call be paged immediately?"}},
)
print(out["answers"])
```

Environment variables:
- `UPSTAGE_API_KEY` — Upstage API key (required). `solar-pro4` currently resolves to `solar-pro4-260806`.
- `TYPESAFE_API_KEY` — only for calling the real Jev during benchmarks (`jev_ref.py`, uses `jev-latest`, which resolved to `jev-1.13.0` for this run)
- `SOLAR_MINI_MODEL` — base model, default `solar-pro4` (`solar-mini4` is faster but less accurate)
- Reasoning is always `none`; the model answers with a single option letter.

## Layout

| path | description |
|------|------|
| `engine.py` | Jev System One questions → Solar chat, default `solar-pro4` (lettered-option prompt) |
| `server.py` | FastAPI `POST /v1/systemone` |
| `jev_ref.py` | Real Jev client (for comparison) |
| `docs/index.html` | API usage page (GitHub Pages) |

## License

Experimental / research code. Do not commit API keys.
