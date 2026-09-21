#!/usr/bin/env python3
"""Freeze Jev answers as gold for a cases JSON (parameterized)."""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_ref import system_one as jev_system_one

WORKERS = 4
MAX_ATTEMPTS = 2


def run_one(case: dict) -> tuple[int, dict | None, str | None]:
    idx = case["idx"]
    last_err = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            j = jev_system_one(case["state"], case["questions"])
            return idx, {
                "model": j.get("model"),
                "answers": j["answers"],
                "latency_s": j.get("latency_s"),
            }, None
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
            print(f"  idx={idx} attempt={attempt} err={last_err}", flush=True)
            if attempt < MAX_ATTEMPTS:
                time.sleep(1.5 * attempt)
    return idx, None, last_err or "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()

    cases_path = Path(args.cases)
    out_path = Path(args.out)
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    gold: dict[str, dict] = {}
    if out_path.exists():
        try:
            gold = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            gold = {}

    todo = [c for c in cases if str(c["idx"]) not in gold or not (gold[str(c["idx"])] or {}).get("answers")]
    print(f"cases={len(cases)} already={len(cases)-len(todo)} todo={len(todo)} workers={args.workers} -> {out_path}", flush=True)
    t0 = time.time()
    errors = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, c): c["idx"] for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            idx, payload, err = fut.result()
            if err or not payload:
                errors += 1
                print(f"[{i}/{len(todo)}] idx={idx} FAIL {err}", flush=True)
            else:
                gold[str(idx)] = payload
                if i % 10 == 0 or i == len(todo):
                    out_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
                print(
                    f"[{i}/{len(todo)}] idx={idx} ok model={payload.get('model')} lat={payload.get('latency_s')}",
                    flush=True,
                )

    out_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wall={time.time()-t0:.1f}s gold_n={len(gold)} errors={errors} -> {out_path}", flush=True)
    if errors:
        missing = [c["idx"] for c in cases if str(c["idx"]) not in gold or not gold[str(c["idx"])].get("answers")]
        print(f"missing_idx={missing}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
