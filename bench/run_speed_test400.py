#!/usr/bin/env python3
"""Speed-only bench: hit System One (local engine or Vercel) on test400.

Does not score accuracy. Reports latency distribution + wall time.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "bench" / "cases_test400.json"


def load_key() -> str:
    key = (os.environ.get("UPSTAGE_API_KEY") or "").strip()
    if key:
        return key
    for p in (Path.home() / ".env", ROOT / ".env"):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if line.startswith("UPSTAGE_API_KEY="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    raise SystemExit("UPSTAGE_API_KEY required")


def call_vercel(base: str, key: str, case: dict, retries: int = 3) -> dict:
    body = {
        "model": "solar-mini4-jev",
        "state": case["state"],
        "questions": case["questions"],
    }
    url = base.rstrip("/") + "/v1/systemone"
    last_err = None
    t0 = time.perf_counter()
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Upstage-Api-Key": key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
                http = resp.status
            wall = time.perf_counter() - t0
            data = json.loads(raw)
            return {
                "idx": case.get("idx"),
                "id": case.get("id"),
                "ok": http == 200 and "answers" in data,
                "http": http,
                "wall_s": round(wall, 4),
                "server_latency_s": data.get("latency_s"),
                "usage": data.get("usage"),
                "n_questions": len(case.get("questions") or {}),
                "attempts": attempt,
            }
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            http = e.code
            wall = time.perf_counter() - t0
            # retry 5xx
            if http >= 500 and attempt < retries:
                time.sleep(0.4 * attempt)
                last_err = f"HTTP {http}: {raw[:200]}"
                continue
            return {
                "idx": case.get("idx"),
                "id": case.get("id"),
                "ok": False,
                "http": http,
                "wall_s": round(wall, 4),
                "server_latency_s": None,
                "error": raw[:300],
                "attempts": attempt,
            }
        except Exception as e:  # noqa: BLE001 — SSL/timeout/network
            last_err = f"{type(e).__name__}: {e}"
            if attempt < retries:
                time.sleep(0.5 * attempt)
                continue
            wall = time.perf_counter() - t0
            return {
                "idx": case.get("idx"),
                "id": case.get("id"),
                "ok": False,
                "http": 0,
                "wall_s": round(wall, 4),
                "server_latency_s": None,
                "error": (last_err or str(e))[:300],
                "attempts": attempt,
            }
    wall = time.perf_counter() - t0
    return {
        "idx": case.get("idx"),
        "id": case.get("id"),
        "ok": False,
        "http": 0,
        "wall_s": round(wall, 4),
        "server_latency_s": None,
        "error": (last_err or "unknown")[:300],
    }



def call_local(key: str, case: dict) -> dict:
    import sys

    sys.path.insert(0, str(ROOT))
    from engine import system_one

    t0 = time.perf_counter()
    try:
        out = system_one(case["state"], case["questions"], api_key=key)
        wall = time.perf_counter() - t0
        return {
            "idx": case.get("idx"),
            "id": case.get("id"),
            "ok": True,
            "http": 200,
            "wall_s": round(wall, 4),
            "server_latency_s": out.get("latency_s"),
            "usage": out.get("usage"),
            "n_questions": len(case.get("questions") or {}),
        }
    except Exception as e:  # noqa: BLE001
        wall = time.perf_counter() - t0
        return {
            "idx": case.get("idx"),
            "id": case.get("id"),
            "ok": False,
            "http": 0,
            "wall_s": round(wall, 4),
            "server_latency_s": None,
            "error": str(e)[:300],
            "n_questions": len(case.get("questions") or {}),
        }


def summarize(rows: list[dict], wall_total: float) -> dict:
    ok = [r for r in rows if r.get("ok")]
    walls = sorted(r["wall_s"] for r in ok if r.get("wall_s") is not None)
    servers = sorted(
        r["server_latency_s"]
        for r in ok
        if isinstance(r.get("server_latency_s"), (int, float))
    )

    def pct(xs: list[float], p: float) -> float | None:
        if not xs:
            return None
        i = min(len(xs) - 1, int(round((p / 100) * (len(xs) - 1))))
        return round(xs[i], 4)

    def dist(xs: list[float]) -> dict:
        if not xs:
            return {}
        return {
            "n": len(xs),
            "avg": round(sum(xs) / len(xs), 4),
            "p50": pct(xs, 50),
            "p90": pct(xs, 90),
            "p95": pct(xs, 95),
            "p99": pct(xs, 99),
            "min": round(xs[0], 4),
            "max": round(xs[-1], 4),
            "sub_1s": round(sum(1 for x in xs if x < 1) / len(xs), 4),
            "sub_0_8s": round(sum(1 for x in xs if x < 0.8) / len(xs), 4),
        }

    return {
        "cases": len(rows),
        "ok": len(ok),
        "fail": len(rows) - len(ok),
        "wall_total_s": round(wall_total, 2),
        "throughput_ok_per_s": round(len(ok) / wall_total, 3) if wall_total else None,
        "client_wall": dist(walls),
        "server_latency_s": dist(servers),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--target",
        choices=("vercel", "local"),
        default="vercel",
        help="vercel = live BYOK API; local = engine.system_one",
    )
    ap.add_argument(
        "--base",
        default=os.environ.get("SYSTEMONE_BASE", "https://solar-mini4-jev.vercel.app"),
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="0 = all cases")
    ap.add_argument(
        "--out",
        default="",
        help="jsonl path (default under bench/)",
    )
    args = ap.parse_args()
    key = load_key()
    cases = json.loads(CASES.read_text())
    if args.limit:
        cases = cases[: args.limit]

    out_path = Path(
        args.out
        or f"bench/speed_{args.target}_test400_w{args.workers}.jsonl"
    )
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    print(
        f"target={args.target} cases={len(cases)} workers={args.workers} base={args.base}",
        flush=True,
    )
    rows: list[dict] = []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        if args.target == "vercel":
            futs = {ex.submit(call_vercel, args.base, key, c): c for c in cases}
        else:
            futs = {ex.submit(call_local, key, c): c for c in cases}
        done = 0
        for fut in as_completed(futs):
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                c = futs[fut]
                row = {
                    "idx": c.get("idx"),
                    "id": c.get("id"),
                    "ok": False,
                    "http": 0,
                    "wall_s": None,
                    "server_latency_s": None,
                    "error": f"{type(e).__name__}: {e}"[:300],
                }
            rows.append(row)
            done += 1
            if done % 25 == 0 or done == len(cases):
                lat = row.get("server_latency_s") or row.get("wall_s")
                print(
                    f"[{done}/{len(cases)}] ok={row.get('ok')} lat={lat}",
                    flush=True,
                )
    wall_total = time.perf_counter() - t0
    rows.sort(key=lambda r: (r.get("idx") is None, r.get("idx") or 0))
    out_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    summary = summarize(rows, wall_total)
    summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
