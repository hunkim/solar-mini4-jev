# Grok 4.6 Judge gold — Solar Mini4 vs Jev (test400)

Official gold: **Grok 4.6 Judge**. Jev is a peer model.

Solar: `solar-mini4-260922` + **`reasoning_effort=none`**.

| model | field_acc | noul≤0.25 | sign@0.5 | choice | score≤1 | miss | avg lat |
|-------|----------:|----------:|---------:|-------:|--------:|-----:|--------:|
| Solar Mini4 | 98.4% | 97.2% | 98.8% | 100% | 100% | 7 | 1.21s |
| Jev | 94.2% | 95.2% | 92.3% | 100% | 85.0% | 26 | 0.38s |

KO / EN field_acc: Solar 98.8 / 98.4 · Jev 93.9 / 94.3

Latency none: p50 1.17s · sub-1s 21.8% · min 0.80s
