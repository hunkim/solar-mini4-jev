# solar-mini4-jev

A drop-in wrapper that exposes Upstage **Solar Mini4** through the TypeSafe Jev System One API shape.

```
POST /v1/systemone
{ "model": "solar-mini4-jev", "state": "...", "questions": { ... } }
```

Supported question types: `noul` | `choice` | `score` (same schema as Jev).

## Official gold: Grok 4.6 Judge

**Jev is not the gold standard.** Jev is a peer model under comparison.
The official scoring reference is the **Grok 4.6 Judge** rubric labels (`bench/gold_grok46_judge_test400.json`).

## Results at a glance

**Judged by an independent grader (Grok 4.6 Judge), Solar Mini4 is right more often than Jev.**
Out of 447 scored answer fields (`reasoning_effort=none`), Solar Mini4 missed **7** and Jev missed **26**. Solar still leads on judged quality; pinning `none` also cuts average latency to **1.21s**.

![Solar Mini4 vs Jev · Grok 4.6 Judge scorecard](bench/infographic_grok46_judge.png)

Jev's misses cluster into two patterns (underrating life-safety situations, treating trivial work as urgent). Solar's misses mostly err on the side of caution.

![Accuracy by metric and diverging cases](bench/infographic_grok46_judge_detail.png)

Interactive scorecard: [view on GitHub Pages](https://hunkim.github.io/solar-mini4-jev/) · [source](docs/index.html)

### test400 @ Grok 4.6 Judge (`solar-mini4` → `solar-mini4-260922`, `reasoning_effort=none`)

| model | field_acc | noul≤0.25 | sign@0.5 | choice | score≤1 | miss | avg latency |
|-------|----------:|----------:|---------:|-------:|--------:|-----:|------------:|
| **Solar Mini4** (`reasoning_effort=none`) | **98.4%** | **97.2%** | **98.8%** | **100%** | **100%** | **7** | **1.21s** |
| Jev 1.13.0 | 94.2% | 95.2% | 92.3% | 100% | 85.0% | 26 | **0.38s** |

Field accuracy by language:

| | KO (n=70 cases) | EN (n=330 cases) |
|--|----------:|-----------:|
| **Solar Mini4** | **98.8%** | **98.4%** |
| Jev | 93.9% | 94.3% |

**Takeaway:** Solar Mini4 wins on judged quality (`none`). Jev wins on speed (~3.2×). p50 latency 1.17s; ~22% of Solar calls are sub-1s.

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
- `SOLAR_REASONING_EFFORT` — default `none` (latency). `medium` is ~10×+ slower

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
| `bench/infographic_grok46_judge*.png` | Scorecard PNG crops used in this README |

## License

Experimental / research code. Do not commit API keys.
