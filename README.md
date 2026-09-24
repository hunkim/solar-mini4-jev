# solar-mini4-jev

A drop-in wrapper that exposes Upstage **Solar Mini4** through the TypeSafe Jev System One API shape.

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

## Public Jev benchmarks (engine v9, 2026-09-24)

Engine v9 = solar-jev prompt with lettered options + rules for solar-mini4 tendencies; one call per question,
`reasoning_effort=none`, ~4 output tokens. Held-out split (not used for tuning), measured from Korea:

| benchmark | n | Jev 1.13.0 | solar-jev (server) | previous wrapper | **v9** |
|---|---:|---:|---:|---:|---:|
| jev-benchmark tool risk | 38 | 94.7 | 94.7 | 89.5 | **92.1** |
| classifier-benchmark v1 | 54 | 98.1 | 87.0 | 81.5 | **87.0** |
| classifier-benchmark v2 | 499 | 96.0 | 86.2 | 71.9 | **84.0** |
| Jevals PubMedQA | 180 | 92.2 | 82.2 | 76.1 | **82.8** |
| Jevals HelpSteer2 | 189 | 38.6 | 35.4 | 40.2 | **32.8** |
| test400 (Grok 4.6 judge) | 260 | 94.6 | 92.7 | 98.5* | **90.8** |
| macro | | 85.7 | 79.7 | 76.3 | **78.2** |
| p50 latency (Korea) | | 624ms | 300ms | 1050ms | **406ms** |

\* the previous wrapper's heuristics were fit to test400. Jev still leads on accuracy; most of Jev's latency
from Korea is network (its API is in us-west-2).

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
- `UPSTAGE_API_KEY` — Solar Mini4 (required). `solar-mini4` currently resolves to `solar-mini4-260922`.
- `TYPESAFE_API_KEY` — only for calling the real Jev during benchmarks (`jev_ref.py`, uses `jev-latest`, which resolved to `jev-1.13.0` for this run)
- `SOLAR_MINI_MODEL` — optional model override
- `WRAP_EVIDENCE_WORDS` — default `0` (label only). e.g. `15` adds a one-line evidence before the label: more accurate, ~300ms slower. Reasoning is always `none`.

## Layout

| path | description |
|------|------|
| `engine.py` | Solar Mini4 + Jev-compatible heuristics |
| `server.py` | FastAPI `POST /v1/systemone` |
| `jev_ref.py` | Real Jev client (for comparison) |
| `bench/gold_grok46_judge_test400.json` | **Official gold** (Grok 4.6 Judge) |
| `bench/gold_jev_test400.json` | Jev response snapshot (peer model) |
| `bench/results_test400_reasoning_none.jsonl` | Solar Mini4 results (`reasoning_effort=none`) |
| `docs/index.html` | Interactive scorecard (GitHub Pages) |

## License

Experimental / research code. Do not commit API keys.
