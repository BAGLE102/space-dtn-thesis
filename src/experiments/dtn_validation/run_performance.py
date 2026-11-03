#!/usr/bin/env python3
"""實驗 B：本方法、sr1、sr10。逐包規劃，前面提交的結果影響後面。

同一時間只跑一個工作，計算時間才不互相干擾。每跑完一組寫入一行，可中斷續跑。
"""
import argparse
import hashlib
import json
import os
import platform
import signal
import time
from fractions import Fraction as Fr

from dtn import ours, srcgr, topology, validate as V
from dtn.model import Problem, arrival


class TimeUp(Exception):
    pass


def _alarm(*_):
    raise TimeUp()


def plan_one(method, P):
    """回傳 (schedule, 未送達原因)。本方法驗證失敗代表演算法有錯，會被標記。"""
    if method == "ours":
        sch = ours.plan(P)
        if not sch:
            return None, "no_route"
        return (sch, "") if V.validate(P, sch) else (None, "VALIDATION_FAILED")
    k = {"sr1": 1, "sr10": 10}[method]
    sch, tried = srcgr.plan(P, k)
    if sch:
        return sch, ""
    return None, "no_route" if tried == 0 else "replay_rejected"


def contact_hash(cs):
    text = "\n".join("%s,%s,%s,%s,%s,%s,%s" % (c.id, c.u, c.v, c.a, c.b, c.r, c.d) for c in cs)
    return hashlib.sha256(text.encode()).hexdigest()


def resources(P, topo_cfg):
    rows = []
    for n, cv in sorted(P.O.items()):
        peak, when = cv.global_peak()
        rows.append(["node_peak_mb", str(n), float(peak), float(when) if when is not None else None])
    util = [sum(y - x for x, y in c.F) / (c.b - c.a) for c in P.cs]
    rows.append(["contact_util_mean", "all", float(sum(util) / len(util)), None])
    rows.append(["contact_util_max", "all", float(max(util)), None])
    return rows


def run_job(name, tc, size, n, m, seed, method, limit):
    params = {k: tc[k] for k in ("nodes", "contacts", "horizon", "min_len", "max_len", "rates", "delays")}
    cs = topology.random_contacts(seed, **params)
    bundles = topology.random_bundles(seed, n, tc["nodes"], tc["release"])
    P = Problem(cs, None, None, Fr(0), Fr(str(size)), Fr(str(m)), {}, Fr(tc["horizon"]))
    rows, status = [], "complete"
    start = time.perf_counter()
    if limit:
        signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(int(limit))
    try:
        for i, (u, v, g) in enumerate(bundles):
            P = P._replace(src=u, dst=v, g=g)
            t0 = time.perf_counter()
            sch, why = plan_one(method, P)
            sec = time.perf_counter() - t0
            row = {"i": i, "src": u, "dst": v, "g": float(g), "sec": round(sec, 6), "why": why}
            if sch:
                row.update(arr=float(arrival(P, sch)), hops=len(sch),
                           path=">".join([str(u)] + [str(c.v) for c, _ in sch]),
                           starts=";".join("%s@%s" % (c.id, float(s)) for c, s in sch))
                P = V.commit(P, sch)
            else:
                row.update(arr=None, hops=0, path="", starts="")
            rows.append(row)
    except TimeUp:
        status = "time_limit"
    finally:
        if limit:
            signal.alarm(0)
    return {"topology": name, "N": n, "M": m, "seed": seed, "method": method, "status": status,
            "wall": round(time.perf_counter() - start, 3), "rows": rows,
            "resources": resources(P, tc), "contact_sha256": contact_hash(cs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="results/performance.jsonl")
    ap.add_argument("--seeds", type=int)
    ap.add_argument("--bundles", type=int, nargs="*")
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding="utf-8"))["performance"]
    seeds = args.seeds or cfg["seeds"]
    grid = args.bundles or cfg["bundles"]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    done = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                done.add((r["topology"], r["N"], r["M"], r["seed"], r["method"]))
    jobs = [(t, n, m, s, me) for t in cfg["topologies"] for n in grid for m in cfg["buffers_mb"]
            for s in range(1, seeds + 1) for me in cfg["methods"]]
    todo = [j for j in jobs if j not in done]
    print("jobs:", len(jobs), "remaining:", len(todo), "python:", platform.python_version(), flush=True)
    with open(args.out, "a", encoding="utf-8") as fh:
        for i, (t, n, m, s, me) in enumerate(todo, 1):
            r = run_job(t, cfg["topologies"][t], cfg["bundle_size_mb"], n, m, s, me,
                        cfg.get("time_limit_per_run_sec"))
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            ok = sum(x["arr"] is not None for x in r["rows"])
            print("%d/%d %s N=%s M=%s seed=%s %s: %d/%d delivered, %.1fs, %s" % (
                i, len(todo), t, n, m, s, me, ok, len(r["rows"]), r["wall"], r["status"]), flush=True)


if __name__ == "__main__":
    main()
