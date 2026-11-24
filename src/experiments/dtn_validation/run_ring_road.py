#!/usr/bin/env python3
"""黃文龍學長的 cross-linked ring road 拓樸：本方法、sr1、sr10。

拓樸：公開 Walker Ring Road contact plan（SHA-256 見 docs/ring_road_contact_plan_source_v01.md），
去掉 Server 節點 48，剩 47 節點、3,172 條連線、0～86,400 秒。

設定（依學長論文，需在論文中註明）：
- 速率：學長論文的 100 KB/s = 0.1 MB/s（原檔為 12,500 B/s，差 8 倍，尚未確認原因）
- Buffer：每個節點 30,000 KB = 30 MB；傳播延遲 0（原檔 range 皆為 0）
- 需求：來源為 cold spot（7–31）或衛星（32–47），目的地為隨機一個 hot spot（1–6），
  大小 300～3,000 KB 均勻取整數 KB，產生時間 0～38,350 秒均勻（約學長生成槽 1～1000），
  期限 86,400 秒。一筆 flow 視為一個不可分割的 bundle。

每跑完一組寫入一行 JSON，可中斷續跑。
"""
import argparse
import hashlib
import json
import os
import random
import time
from fractions import Fraction as Fr

from dtn import ours, runio, srcgr, validate as V
from dtn.model import Contact, Problem, arrival

SHA = "fe363dabdd182e292f5e3b74a28558245b2caf9d3aa7730db60d52afdb9763d2"
HOT, COLD, SAT = range(1, 7), range(7, 32), range(32, 48)


def load_contacts(path, rate):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit("contact plan 的 SHA-256 不符")
    cs = []
    for line in raw.decode().splitlines():
        p = line.split()
        if len(p) != 7 or p[1] != "contact":
            continue
        a, b, u, v = int(p[2]), int(p[3]), int(p[4]), int(p[5])
        if u == 48 or v == 48:
            continue
        cs.append(Contact("rr%d" % len(cs), u, v, Fr(a), Fr(b), rate, Fr(0), ()))
    assert len(cs) == 3172, len(cs)
    return cs


def demands(seed, n, release):
    rng = random.Random("ringroad-%s" % seed)
    srcs = list(COLD) + list(SAT)
    res = []
    for _ in range(n):
        res.append((rng.choice(srcs), rng.choice(list(HOT)), Fr(rng.randint(0, release)),
                    Fr(rng.randint(300, 3000), 1000)))
    res.sort(key=lambda x: x[2])
    return res


def plan_one(method, P):
    if method == "ours":
        sch = ours.plan(P)
        if not sch:
            return None, "no_route"
        return (sch, "") if V.validate(P, sch) else (None, "VALIDATION_FAILED")
    sch, tried = srcgr.plan(P, {"sr1": 1, "sr10": 10}[method])
    if sch:
        return sch, ""
    return None, "no_route" if tried == 0 else "replay_rejected"


def run_job(cs, seed, n, M, method, ct, release, T):
    P = Problem(cs, None, None, Fr(0), Fr(1), M, {}, T, ct)
    rows = []
    for i, (u, v, g, S) in enumerate(demands(seed, n, release)):
        P = P._replace(src=u, dst=v, g=g, S=S)
        t0 = time.perf_counter()
        sch, why = plan_one(method, P)
        sec = time.perf_counter() - t0
        if sch:
            arr = arrival(P, sch)
            P = V.commit(P, sch)
            rows.append(dict(i=i, src=u, dst=v, g=float(g), size_mb=float(S), arr=float(arr),
                             hops=len(sch), path=">".join(str(c.u) for c, _ in sch) + ">%d" % sch[-1][0].v,
                             sec=sec, why=""))
        else:
            rows.append(dict(i=i, src=u, dst=v, g=float(g), size_mb=float(S), arr=None, hops=None,
                             path=None, sec=sec, why=why))
    peaks = {str(n): float(cv.global_peak()[0]) for n, cv in P.O.items()}
    return rows, peaks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="../../../tmp/topology_sources/"
                    "RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt")
    ap.add_argument("--flows", type=int, nargs="+", default=[50, 100, 175])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--methods", nargs="+", default=["ours", "sr1", "sr10"])
    ap.add_argument("--buffer-mb", type=Fr, default=Fr(30))
    ap.add_argument("--rate-mbps", type=Fr, default=Fr(1, 10))
    ap.add_argument("--release", type=int, default=38350)
    ap.add_argument("--cut-through", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cs = load_contacts(a.plan, a.rate_mbps)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    done = runio.load_done(a.out, lambda r: (r["flows"], r["seed"], r["method"]), runio.no_validation_failure)
    with open(a.out, "a") as fh:
        for n in a.flows:
            for seed in range(1, a.seeds + 1):
                for m in a.methods:
                    if (n, seed, m) in done:
                        continue
                    t0 = time.perf_counter()
                    rows, peaks = run_job(cs, seed, n, a.buffer_mb, m, a.cut_through, a.release, Fr(86400))
                    ok = sum(r["arr"] is not None for r in rows)
                    rec = dict(flows=n, seed=seed, method=m, ct=a.cut_through,
                               buffer_mb=float(a.buffer_mb), rate_mbps=float(a.rate_mbps),
                               delivered=ok, total=len(rows), wall=time.perf_counter() - t0,
                               rows=rows, node_peak_mb=peaks)
                    if not runio.no_validation_failure([rec]):
                        runio.record_failure_and_stop(a.out, rec, "flows=%d seed=%d %s" % (n, seed, m))
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    print("flows=%d seed=%d %s: %d/%d, %.1fs" % (n, seed, m, ok, len(rows),
                                                                 time.perf_counter() - t0), flush=True)


if __name__ == "__main__":
    main()
