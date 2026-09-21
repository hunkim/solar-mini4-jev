#!/usr/bin/env python3
"""Run 200 cases on Jev (gold) and solar-mini4-jev; compare latency + agreement."""
from __future__ import annotations

import json
import math
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import system_one as solar_system_one
from jev_ref import system_one as jev_system_one

CASES = json.loads((Path(__file__).parent / "cases.json").read_text())
OUT = Path(__file__).parent / "results.jsonl"
SUMMARY = Path(__file__).parent / "summary.json"
WORKERS = 4


def agree_noul(a: float, b: float, tol: float = 0.25) -> bool:
    return abs(a - b) <= tol


def agree_choice(a: dict, b: dict) -> bool:
    return (a or {}).get("choice") == (b or {}).get("choice")


def agree_score(a: float, b: float, tol: float = 1.0) -> bool:
    return abs(a - b) <= tol


def compare_answers(qs: dict, gold: dict, pred: dict) -> dict:
    per = {}
    for name, q in qs.items():
        g = gold.get(name) or {}
        p = pred.get(name) or {}
        t = q.get("type")
        if t == "noul":
            gv, pv = float(g.get("noul", 0.5)), float(p.get("noul", 0.5))
            per[name] = {
                "type": t,
                "gold": gv,
                "pred": pv,
                "abs_err": abs(gv - pv),
                "agree_tol0.25": agree_noul(gv, pv),
                "agree_sign0.5": (gv >= 0.5) == (pv >= 0.5),
            }
        elif t == "choice":
            per[name] = {
                "type": t,
                "gold": g.get("choice"),
                "pred": p.get("choice"),
                "agree": agree_choice(g, p),
            }
        elif t == "score":
            gv, pv = float(g.get("score", 0)), float(p.get("score", 0))
            per[name] = {
                "type": t,
                "gold": gv,
                "pred": pv,
                "abs_err": abs(gv - pv),
                "agree_tol1": agree_score(gv, pv),
            }
    return per


def run_one(case: dict) -> dict:
    row = {
        "idx": case["idx"],
        "id": case["id"],
        "kind": case["kind"],
        "error": None,
    }
    try:
        j = jev_system_one(case["state"], case["questions"])
        s = solar_system_one(case["state"], case["questions"])
        row["jev"] = {
            "model": j["model"],
            "answers": j["answers"],
            "latency_s": j["latency_s"],
            "usage": j.get("usage"),
        }
        row["solar"] = {
            "model": s["model"],
            "answers": s["answers"],
            "latency_s": s["latency_s"],
            "usage": s.get("usage"),
        }
        row["compare"] = compare_answers(case["questions"], j["answers"], s["answers"])
    except Exception as e:  # noqa: BLE001
        row["error"] = f"{type(e).__name__}: {e}"
        row["trace"] = traceback.format_exc()[-800:]
    return row


def main() -> None:
    done = {}
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["idx"]] = r
    todo = [c for c in CASES if c["idx"] not in done or done[c["idx"]].get("error")]
    # rewrite errored
    if todo and OUT.exists():
        keep = [done[i] for i in sorted(done) if i not in {c["idx"] for c in todo}]
        OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")

    print(f"todo={len(todo)}/{len(CASES)} workers={WORKERS}", flush=True)
    t0 = time.time()
    with OUT.open("a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(run_one, c): c["idx"] for c in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                row = fut.result()
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                ok = not row.get("error")
                jl = (row.get("jev") or {}).get("latency_s")
                sl = (row.get("solar") or {}).get("latency_s")
                print(
                    f"[{i}/{len(todo)}] idx={row['idx']} kind={row['kind']} "
                    f"ok={ok} jev={jl}s solar={sl}s",
                    flush=True,
                )
    print(f"wall={time.time()-t0:.1f}s", flush=True)

    rows = [json.loads(l) for l in OUT.read_text().splitlines() if l.strip()]
    by_idx = {r["idx"]: r for r in rows}
    rows = [by_idx[c["idx"]] for c in CASES if c["idx"] in by_idx]

    def avg(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    noul_err, noul_tol, noul_sign = [], [], []
    choice_ok, score_err, score_tol = [], [], []
    jev_lat, sol_lat = [], []
    errors = 0
    for r in rows:
        if r.get("error"):
            errors += 1
            continue
        jev_lat.append(r["jev"]["latency_s"])
        sol_lat.append(r["solar"]["latency_s"])
        for name, c in (r.get("compare") or {}).items():
            if c["type"] == "noul":
                noul_err.append(c["abs_err"])
                noul_tol.append(1 if c["agree_tol0.25"] else 0)
                noul_sign.append(1 if c["agree_sign0.5"] else 0)
            elif c["type"] == "choice":
                choice_ok.append(1 if c["agree"] else 0)
            elif c["type"] == "score":
                score_err.append(c["abs_err"])
                score_tol.append(1 if c["agree_tol1"] else 0)

    summary = {
        "n_cases": len(rows),
        "errors": errors,
        "latency": {
            "jev_avg_s": avg(jev_lat),
            "solar_avg_s": avg(sol_lat),
            "jev_p50_s": avg(sorted(jev_lat)[len(jev_lat)//2:len(jev_lat)//2+1]) if jev_lat else None,
            "solar_p50_s": avg(sorted(sol_lat)[len(sol_lat)//2:len(sol_lat)//2+1]) if sol_lat else None,
            "speedup_jev_over_solar": round((avg(sol_lat) or 0) / (avg(jev_lat) or 1), 2),
        },
        "noul": {
            "n": len(noul_err),
            "mae": round(sum(noul_err) / len(noul_err), 4) if noul_err else None,
            "agree_within_0.25": round(sum(noul_tol) / len(noul_tol), 4) if noul_tol else None,
            "agree_sign_at_0.5": round(sum(noul_sign) / len(noul_sign), 4) if noul_sign else None,
        },
        "choice": {
            "n": len(choice_ok),
            "exact_match": round(sum(choice_ok) / len(choice_ok), 4) if choice_ok else None,
        },
        "score": {
            "n": len(score_err),
            "mae": round(sum(score_err) / len(score_err), 4) if score_err else None,
            "agree_within_1": round(sum(score_tol) / len(score_tol), 4) if score_tol else None,
        },
        "gold": "TypeSafe Jev (jev-latest)",
        "pred": "solar-mini4-jev wrapper",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
