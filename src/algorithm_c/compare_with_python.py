#!/usr/bin/env python3
"""比對 C 版與 Python 版：同樣的案例，逐包比較排程是否完全相同。

在 src/algorithm_c 底下執行（先 make）：
    python3 compare_with_python.py              小案例 500 個 × 兩種轉送方式
    python3 compare_with_python.py --small 3000 --random 3

小案例：src/experiments/dtn_validation 的 small_case（含背景占用、多包依序提交）。
隨機拓樸：random_20n（20 節點、600 連線），每包 1 MB、Buffer 3 MB、100 包。
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
sys.path[:0] = [SRC, os.path.join(SRC, "experiments", "dtn_validation")]

from algorithm import model as rm, ours as ro, validate as rv   # noqa: E402
from dtn import topology                                           # noqa: E402


def to_input(P, bundles, nodes):
    """把 Problem 與需求寫成 C 版的輸入檔格式。"""
    lines = ["nodes %d" % nodes]
    for c in P.cs:
        lines.append("contact %s %d %d %s %s %s %s" % (c.id, c.u, c.v, c.a, c.b, c.r, c.d))
    for n, cv in sorted(P.O.items()):
        pts = " ".join("%s %s %s" % x for x in zip(cv.ts, cv.ls, cv.rs))
        lines.append("background %d %s" % (n, pts))
    lines.append("param %s %s %s %d" % (P.S, P.M, P.T, 1 if P.ct else 0))
    for u, v, g in bundles:
        lines.append("bundle %d %d %s" % (u, v, g))
    return "\n".join(lines) + "\n"


def python_lines(P, bundles):
    """Python 版的逐包輸出，格式和 C 版相同。"""
    out = []
    for i, (u, v, g) in enumerate(bundles):
        P = P._replace(src=u, dst=v, g=g)
        sch = ro.plan(P)
        if not sch:
            out.append("bundle %d: none" % i)
            continue
        if not rv.validate(P, sch):
            out.append("bundle %d: VALIDATION_FAILED" % i)
            continue
        out.append("bundle %d: arr %s %s" % (i, rm.arrival(P, sch), " ".join("%s@%s" % (c.id, s) for c, s in sch)))
        P = rv.commit(P, sch)
    return out


def run_c(text):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    t0 = time.perf_counter()
    res = subprocess.run([os.path.join(HERE, "dtn"), path], capture_output=True, text=True)
    sec = time.perf_counter() - t0
    os.unlink(path)
    if res.returncode:
        raise RuntimeError(res.stderr)
    return res.stdout.strip().splitlines(), sec


def compare(name, P, bundles, nodes, stats):
    t0 = time.perf_counter()
    want = python_lines(P, bundles)
    stats["py"] += time.perf_counter() - t0
    got, sec = run_c(to_input(P, bundles, nodes))
    stats["c"] += sec
    stats["bundles"] += len(want)
    for w, g in zip(want, got):
        if w != g:
            stats["diff"] += 1
            if stats["diff"] <= 5:
                print("  不同：%s\n    Python：%s\n    C     ：%s" % (name, w, g))
    if len(want) != len(got):
        stats["diff"] += 1
        print("  行數不同：%s" % name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", type=int, default=500)
    ap.add_argument("--random", type=int, default=0, help="random_20n 的種子數")
    args = ap.parse_args()

    for ct in (False, True):
        stats = dict(bundles=0, diff=0, py=0.0, c=0.0)
        for seed in range(1, args.small + 1):
            P, bundles = topology.small_case(seed)
            P = rm.Problem(*P)._replace(ct=ct)
            nodes = 1 + max([c.u for c in P.cs] + [c.v for c in P.cs] + list(P.O) + [x for b in bundles for x in b[:2]])
            compare("小案例 %d" % seed, P, bundles, nodes, stats)
        print("小案例（%s）：%d 包，不同 %d" % ("邊收邊轉" if ct else "收完才轉", stats["bundles"], stats["diff"]))

    cfg = dict(nodes=20, contacts=600, horizon=3600, min_len=30, max_len=300,
               rates=[1, 2, 5], delays=[0, 0.1, 0.25, 0.5])
    for ct in (False, True):
        if not args.random:
            break
        stats = dict(bundles=0, diff=0, py=0.0, c=0.0)
        for seed in range(1, args.random + 1):
            cs = topology.random_contacts(seed, **cfg)
            bundles = topology.random_bundles(seed, 100, 20, 600)
            P = rm.Problem(cs, None, None, Fr(0), Fr(1), Fr(3), {}, Fr(3600), ct)
            compare("random_20n seed %d" % seed, P, bundles, 20, stats)
        print("random_20n（%s）：%d 包，不同 %d；Python %.1f 秒、C %.1f 秒" % (
            "邊收邊轉" if ct else "收完才轉", stats["bundles"], stats["diff"], stats["py"], stats["c"]))


if __name__ == "__main__":
    main()
