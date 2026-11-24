#!/usr/bin/env python3
"""實驗 A：本方法對格點窮舉（單包最早抵達，含多包提交後的背景）。可中斷續跑。"""
import argparse
import json
import os
import sys
import time
from fractions import Fraction as Fr

from dtn import ours, oracle, runio, topology, validate as V
from dtn.model import arrival


def classify(a, o):
    if a is None and o is None:
        return "both_none"
    if a is None:
        return "missed"
    if o is None:
        return "extra"
    return "same" if a == o else ("earlier" if a < o else "later")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="results/validation.jsonl")
    ap.add_argument("--cases", type=int)
    ap.add_argument("--cut-through", action="store_true", help="中繼可邊收邊送（P.ct=True）")
    ap.add_argument("--known-later", type=int, nargs="*", default=[],
                    help="已知且已解釋的 later 案例（例如違反背景假設的案例），不視為失敗")
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding="utf-8"))["validation"]
    cases = args.cases or cfg["cases"]
    grid = Fr(1, cfg["grid_denominator"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    done = runio.load_done(args.out, lambda r: r["case"])
    bad = 0
    with open(args.out, "a", encoding="utf-8") as fh:
        for seed in range(cfg["first_seed"], cfg["first_seed"] + cases):
            if seed in done:
                continue
            P, bundles = topology.small_case(seed)
            P = P._replace(ct=args.cut_through)
            lines = []
            for idx, (u, v, g) in enumerate(bundles):
                P = P._replace(src=u, dst=v, g=g)
                t0 = time.perf_counter()
                sch = ours.plan(P)
                t1 = time.perf_counter()
                o = oracle.earliest(P, grid)
                t2 = time.perf_counter()
                a = arrival(P, sch) if sch else None
                ok = V.validate(P, sch) if sch else None
                kind = classify(a, o)
                bad += kind in ("missed", "extra", "later") or ok is False
                if kind in ("missed", "extra") or ok is False:
                    sys.exit("驗證失敗，停止：case %d bundle %d，result=%s，replay_ok=%s" % (seed, idx, kind, ok))
                lines.append(json.dumps({
                    "case": seed, "bundle": idx, "src": u, "dst": v, "g": float(g),
                    "ours": float(a) if a is not None else None,
                    "oracle": float(o) if o is not None else None,
                    "result": kind, "replay_ok": ok,
                    "ours_sec": round(t1 - t0, 6), "oracle_sec": round(t2 - t1, 6)}) + "\n")
                if sch and ok:
                    P = V.commit(P, sch)
            fh.write("".join(lines))  # 一個案例整批寫入，避免中斷時只留一部分
            fh.flush()
            if (seed - cfg["first_seed"] + 1) % 100 == 0:
                print("validation", seed - cfg["first_seed"] + 1, "/", cases, "problems:", bad, flush=True)
    print("validation finished; new problems:", bad)
    with open(args.out, encoding="utf-8") as fh:  # 含之前跑過的部分
        later = [r["case"] for r in map(json.loads, fh) if r["result"] == "later"]
    unknown = sorted(set(later) - set(args.known_later))
    if later:
        print("later cases:", sorted(set(later)), flush=True)
    if unknown:
        sys.exit("出現未解釋的 later 案例，停止：%s" % unknown)


if __name__ == "__main__":
    main()
