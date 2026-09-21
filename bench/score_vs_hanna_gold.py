#!/usr/bin/env python3
"""Score Solar results (jsonl) and optional Jev gold against Hanna gold."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def compare_field(qtype: str, g: dict, p: dict) -> dict:
    if qtype == "noul":
        gv, pv = float(g.get("noul", 0.5)), float(p.get("noul", 0.5))
        return {
            "type": qtype, "gold": gv, "pred": pv, "abs_err": abs(gv - pv),
            "agree_tol0.25": abs(gv - pv) <= 0.25,
            "agree_sign0.5": (gv >= 0.5) == (pv >= 0.5),
        }
    if qtype == "choice":
        return {
            "type": qtype, "gold": g.get("choice"), "pred": p.get("choice"),
            "agree": g.get("choice") == p.get("choice"),
        }
    if qtype == "score":
        gv, pv = float(g.get("score", 0)), float(p.get("score", 0))
        return {
            "type": qtype, "gold": gv, "pred": pv, "abs_err": abs(gv - pv),
            "agree_tol1": abs(gv - pv) <= 1.0,
        }
    return {"type": qtype, "agree": False}


def summarize_pairs(cases, gold_map, pred_map, label_gold, label_pred, pred_is_row=False):
    """pred_map: idx -> answers dict, or idx -> full result row if pred_is_row."""
    def avg(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    noul_err, noul_tol, noul_sign = [], [], []
    choice_ok, score_err, score_tol = [], [], []
    errors = 0
    misses = []
    lat = []

    for c in cases:
        idx = c["idx"]
        gentry = gold_map.get(idx) or gold_map.get(str(idx))
        if not gentry:
            errors += 1
            continue
        gans = gentry.get("answers") or gentry

        if pred_is_row:
            row = pred_map.get(idx)
            if not row or row.get("error") or not (row.get("solar") or {}).get("answers"):
                errors += 1
                continue
            pans = row["solar"]["answers"]
            if row["solar"].get("latency_s") is not None:
                lat.append(row["solar"]["latency_s"])
        else:
            pentry = pred_map.get(idx) or pred_map.get(str(idx))
            if not pentry:
                errors += 1
                continue
            pans = pentry.get("answers") or pentry

        for name, q in c["questions"].items():
            t = q.get("type")
            cmp = compare_field(t, gans.get(name) or {}, pans.get(name) or {})
            if t == "noul":
                noul_err.append(cmp["abs_err"])
                noul_tol.append(int(cmp["agree_tol0.25"]))
                noul_sign.append(int(cmp["agree_sign0.5"]))
                if not cmp["agree_tol0.25"] or not cmp["agree_sign0.5"]:
                    misses.append({"id": c["id"], "field": name, "detail": cmp})
            elif t == "choice":
                choice_ok.append(int(cmp["agree"]))
                if not cmp["agree"]:
                    misses.append({"id": c["id"], "field": name, "detail": cmp})
            elif t == "score":
                score_err.append(cmp["abs_err"])
                score_tol.append(int(cmp["agree_tol1"]))
                if not cmp["agree_tol1"]:
                    misses.append({"id": c["id"], "field": name, "detail": cmp})

    summary = {
        "n_cases": len(cases),
        "errors": errors,
        "latency": {"solar_avg_s": avg(lat)} if lat else {},
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
        "miss_count": len(misses),
        "misses": misses,
        "gold": label_gold,
        "pred": label_pred,
    }
    summary["perfect_on_thresholds"] = (
        summary["noul"]["agree_within_0.25"] == 1
        and summary["noul"]["agree_sign_at_0.5"] == 1
        and summary["choice"]["exact_match"] == 1
        and summary["score"]["agree_within_1"] == 1
        and errors == 0
    )
    return summary


def divergence_themes(cases, hanna, jev, solar_rows):
    """Find Jev≠Hanna fields; note when Solar matches Hanna."""
    by_idx = {r["idx"]: r for r in solar_rows}
    themes = Counter()
    examples = []
    for c in cases:
        idx = c["idx"]
        h = (hanna.get(idx) or hanna.get(str(idx)) or {}).get("answers") or {}
        j = (jev.get(idx) or jev.get(str(idx)) or {}).get("answers") or {}
        row = by_idx.get(idx) or {}
        s = ((row.get("solar") or {}).get("answers")) or {}
        for name, q in c["questions"].items():
            t = q.get("type")
            hg, jg, sg = h.get(name) or {}, j.get(name) or {}, s.get(name) or {}
            diverge = False
            solar_match_h = False
            detail = {}
            if t == "noul":
                hv, jv = float(hg.get("noul", 0.5)), float(jg.get("noul", 0.5))
                sv = float(sg.get("noul", 0.5)) if sg else None
                if abs(hv - jv) > 0.25 or (hv >= 0.5) != (jv >= 0.5):
                    diverge = True
                    detail = {"type": t, "hanna": hv, "jev": jv, "solar": sv}
                    if sv is not None and abs(hv - sv) <= 0.25 and (hv >= 0.5) == (sv >= 0.5):
                        solar_match_h = True
                    # theme
                    if jv < 0.55 <= hv:
                        themes["jev_low_hanna_mid_or_high"] += 1
                    elif hv < 0.55 <= jv:
                        themes["jev_high_hanna_low"] += 1
                    elif abs(hv - jv) > 0.25 and 0.4 <= hv <= 0.75 and jv < 0.5:
                        themes["hanna_mid_jev_under"] += 1
                    elif hv >= 0.85 and jv < 0.7:
                        themes["hanna_cat_jev_under"] += 1
                    elif 0.55 <= hv <= 0.75 and jv >= 0.85:
                        themes["hanna_mid_jev_overshoot"] += 1
                    elif 0.4 <= hv <= 0.6 and jv >= 0.7:
                        themes["hanna_soft_jev_overshoot"] += 1
                    else:
                        themes["noul_other_diverge"] += 1
            elif t == "choice":
                if hg.get("choice") != jg.get("choice"):
                    diverge = True
                    detail = {"type": t, "hanna": hg.get("choice"), "jev": jg.get("choice"), "solar": sg.get("choice")}
                    solar_match_h = sg.get("choice") == hg.get("choice")
                    themes[f"choice_{c['id'].split('_')[2] if '_' in c['id'] else 'x'}"] += 1
            elif t == "score":
                hv, jv = float(hg.get("score", 0)), float(jg.get("score", 0))
                sv = float(sg.get("score", 0)) if sg else None
                if abs(hv - jv) > 1.0:
                    diverge = True
                    detail = {"type": t, "hanna": hv, "jev": jv, "solar": sv}
                    solar_match_h = sv is not None and abs(hv - sv) <= 1.0
                    themes["score_tol"] += 1
            if diverge:
                examples.append({
                    "id": c["id"], "field": name, "detail": detail,
                    "solar_matches_hanna": solar_match_h,
                    "state_preview": c["state"][:120],
                })
    solar_match_examples = [e for e in examples if e["solar_matches_hanna"]][:12]
    return {
        "n_diverge_fields": len(examples),
        "theme_counts": dict(themes.most_common(20)),
        "examples_solar_matches_hanna": solar_match_examples,
        "examples_all_head": examples[:15],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(Path(__file__).parent / "cases_test400.json"))
    ap.add_argument("--hanna", default=str(Path(__file__).parent / "gold_hanna_test400.json"))
    ap.add_argument("--results", default=str(Path(__file__).parent / "results_test400_final_v3.jsonl"))
    ap.add_argument("--jev", default=str(Path(__file__).parent / "gold_jev_test400.json"))
    ap.add_argument("--summary-solar", default=str(Path(__file__).parent / "summary_test400_hanna_gold.json"))
    ap.add_argument("--summary-jev", default=str(Path(__file__).parent / "summary_jev_vs_hanna_test400.json"))
    args = ap.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    hanna = {int(k): v for k, v in json.loads(Path(args.hanna).read_text(encoding="utf-8")).items()}
    jev = {int(k): v for k, v in json.loads(Path(args.jev).read_text(encoding="utf-8")).items()}
    rows = [json.loads(l) for l in Path(args.results).read_text().splitlines() if l.strip()]
    by_idx = {r["idx"]: r for r in rows}

    solar_sum = summarize_pairs(
        cases, hanna, by_idx,
        "Hanna gold gold_hanna_test400.json",
        "solar from results_test400_final_v3.jsonl",
        pred_is_row=True,
    )
    Path(args.summary_solar).write_text(json.dumps(solar_sum, ensure_ascii=False, indent=2), encoding="utf-8")

    jev_sum = summarize_pairs(
        cases, hanna, jev,
        "Hanna gold gold_hanna_test400.json",
        "Jev gold gold_jev_test400.json",
        pred_is_row=False,
    )
    div = divergence_themes(cases, hanna, jev, rows)
    jev_sum["divergence_vs_hanna"] = div
    Path(args.summary_jev).write_text(json.dumps(jev_sum, ensure_ascii=False, indent=2), encoding="utf-8")

    def brief(s):
        return {k: v for k, v in s.items() if k not in ("misses", "divergence_vs_hanna")} | {
            "miss_count": s.get("miss_count"),
            "themes": (s.get("divergence_vs_hanna") or {}).get("theme_counts"),
        }

    print("=== Solar @ Hanna ===", flush=True)
    print(json.dumps(brief(solar_sum), ensure_ascii=False, indent=2), flush=True)
    print("=== Jev @ Hanna ===", flush=True)
    print(json.dumps(brief(jev_sum), ensure_ascii=False, indent=2), flush=True)

    # print a few Solar-matches-Hanna where Jev diverges
    print("=== Example Jev≠Hanna where Solar≈Hanna ===", flush=True)
    for e in div["examples_solar_matches_hanna"][:8]:
        print(json.dumps(e, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
