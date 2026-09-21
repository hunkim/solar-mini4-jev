#!/usr/bin/env python3
"""Freeze Jev answers as gold for holdout cases_v2.json."""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from jev_ref import system_one as jev_system_one

CASES = json.loads((Path(__file__).parent / "cases_v2.json").read_text(encoding="utf-8"))
OUT = Path(__file__).parent / "gold_jev_v2.json"
WORKERS = 4
MAX_ATTEMPTS = 2  # initial + one retry


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
    gold: dict[str, dict] = {}
    if OUT.exists():
        try:
            gold = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            gold = {}

    todo = [c for c in CASES if str(c["idx"]) not in gold or not (gold[str(c["idx"])] or {}).get("answers")]
    print(f"cases={len(CASES)} already={len(gold)} todo={len(todo)} workers={WORKERS}", flush=True)
    t0 = time.time()
    errors = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(run_one, c): c["idx"] for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            idx, payload, err = fut.result()
            if err or not payload:
                errors += 1
                print(f"[{i}/{len(todo)}] idx={idx} FAIL {err}", flush=True)
            else:
                gold[str(idx)] = payload
                # checkpoint periodically
                if i % 10 == 0 or i == len(todo):
                    OUT.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
                print(
                    f"[{i}/{len(todo)}] idx={idx} ok model={payload.get('model')} "
                    f"lat={payload.get('latency_s')}",
                    flush=True,
                )

    OUT.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wall={time.time()-t0:.1f}s gold_n={len(gold)} errors={errors} -> {OUT}", flush=True)
    if errors:
        missing = [c["idx"] for c in CASES if str(c["idx"]) not in gold]
        print(f"missing_idx={missing}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
