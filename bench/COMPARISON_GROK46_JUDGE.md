# Grok 4.6 Judge gold — Solar Mini4 vs Jev (test400)

Official gold: **Grok 4.6 Judge** (`gold_grok46_judge_test400.json`).  
Jev is evaluated as a peer model, not as gold.

Solar backend: `solar-mini4` → `solar-mini4-260922` (2026-09-21 re-run).

| model | field_acc | noul≤0.25 | sign@0.5 | choice | score≤1 | miss | avg lat |
|-------|----------:|----------:|---------:|-------:|--------:|-----:|--------:|
| Solar Mini4 | 98.7% | 97.6% | 98.8% | 100% | 100% | 6 | 1.41s |
| Jev | 94.2% | 95.2% | 92.3% | 100% | 85.0% | 26 | 0.38s |

KO / EN field_acc: Solar 98.8 / 98.6 · Jev 93.9 / 94.3
