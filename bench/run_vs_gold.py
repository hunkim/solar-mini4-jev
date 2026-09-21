#!/usr/bin/env python3
"""Re-score solar-mini4-jev against frozen Jev gold (no Jev re-calls)."""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import system_one as solar_system_one

CASES = json.loads((Path(__file__).parent / "cases.json").read_text())
GOLD = {int(k): v for k, v in json.loads((Path(__file__).parent / "gold_jev.json").read_text()).items()}
OUT = Path(__file__).parent / "results_v3.jsonl"
SUMMARY = Path(__file__).parent / "summary_v3.json"
WORKERS = 4


def compare(qs, gold, pred):
    per = {}
    for name, q in qs.items():
        g, p = gold.get(name) or {}, pred.get(name) or {}
        t = q.get("type")
        if t == "noul":
            gv, pv = float(g.get("noul", 0.5)), float(p.get("noul", 0.5))
            per[name] = {
                "type": t, "gold": gv, "pred": pv, "abs_err": abs(gv - pv),
                "agree_tol0.25": abs(gv - pv) <= 0.25,
                "agree_sign0.5": (gv >= 0.5) == (pv >= 0.5),
            }
        elif t == "choice":
            per[name] = {"type": t, "gold": g.get("choice"), "pred": p.get("choice"), "agree": g.get("choice") == p.get("choice")}
        elif t == "score":
            gv, pv = float(g.get("score", 0)), float(p.get("score", 0))
            per[name] = {
                "type": t, "gold": gv, "pred": pv, "abs_err": abs(gv - pv),
                "agree_tol1": abs(gv - pv) <= 1.0,
            }
    return per


def run_one(case):
    row = {"idx": case["idx"], "id": case["id"], "kind": case["kind"], "error": None}
    g = GOLD.get(case["idx"])
    if not g:
        row["error"] = "missing gold"
        return row
    try:
        s = solar_system_one(case["state"], case["questions"])
        row["jev"] = {"model": g.get("model"), "answers": g["answers"], "latency_s": g.get("latency_s")}
        row["solar"] = {"model": s["model"], "answers": s["answers"], "latency_s": s["latency_s"]}
        row["compare"] = compare(case["questions"], g["answers"], s["answers"])
    except Exception as e:
        row["error"] = f"{type(e).__name__}: {e}"
        row["trace"] = traceback.format_exc()[-600:]
    return row


def main():
    if OUT.exists():
        OUT.unlink()
    print(f"cases={len(CASES)} gold={len(GOLD)} workers={WORKERS}", flush=True)
    t0 = time.time()
    with OUT.open("w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(run_one, c): c["idx"] for c in CASES}
            for i, fut in enumerate(as_completed(futs), 1):
                row = fut.result()
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                ok = not row.get("error")
                print(f"[{i}/{len(CASES)}] idx={row['idx']} ok={ok} solar={(row.get('solar') or {}).get('latency_s')}", flush=True)
    print(f"wall={time.time()-t0:.1f}s", flush=True)

    rows = [json.loads(l) for l in OUT.read_text().splitlines() if l.strip()]
    by = {r["idx"]: r for r in rows}
    rows = [by[c["idx"]] for c in CASES if c["idx"] in by]

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    noul_err, noul_tol, noul_sign, choice_ok, score_err, score_tol = [], [], [], [], [], []
    sol_lat, errors = [], 0
    misses = []
    for r in rows:
        if r.get("error"):
            errors += 1
            continue
        sol_lat.append(r["solar"]["latency_s"])
        for name, c in (r.get("compare") or {}).items():
            if c["type"] == "noul":
                noul_err.append(c["abs_err"]); noul_tol.append(int(c["agree_tol0.25"])); noul_sign.append(int(c["agree_sign0.5"]))
                if not c["agree_tol0.25"] or not c["agree_sign0.5"]:
                    misses.append((r["id"], name, c))
            elif c["type"] == "choice":
                choice_ok.append(int(c["agree"]))
                if not c["agree"]:
                    misses.append((r["id"], name, c))
            elif c["type"] == "score":
                score_err.append(c["abs_err"]); score_tol.append(int(c["agree_tol1"]))
                if not c["agree_tol1"]:
                    misses.append((r["id"], name, c))

    summary = {
        "n_cases": len(rows),
        "errors": errors,
        "latency": {"solar_avg_s": avg(sol_lat)},
        "noul": {
            "n": len(noul_err),
            "mae": round(sum(noul_err)/len(noul_err),4) if noul_err else None,
            "agree_within_0.25": round(sum(noul_tol)/len(noul_tol),4) if noul_tol else None,
            "agree_sign_at_0.5": round(sum(noul_sign)/len(noul_sign),4) if noul_sign else None,
        },
        "choice": {"n": len(choice_ok), "exact_match": round(sum(choice_ok)/len(choice_ok),4) if choice_ok else None},
        "score": {
            "n": len(score_err),
            "mae": round(sum(score_err)/len(score_err),4) if score_err else None,
            "agree_within_1": round(sum(score_tol)/len(score_tol),4) if score_tol else None,
        },
        "misses": [{"id": a, "field": b, "detail": c} for a,b,c in misses],
        "gold": "frozen Jev from gold_jev.json",
        "pred": "solar-mini4-jev v3",
    }
    # perfect?
    perfect = (
        (summary["noul"]["agree_within_0.25"] == 1 and summary["noul"]["agree_sign_at_0.5"] == 1)
        and summary["choice"]["exact_match"] == 1
        and summary["score"]["agree_within_1"] == 1
        and errors == 0
    )
    summary["perfect_on_thresholds"] = perfect
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
