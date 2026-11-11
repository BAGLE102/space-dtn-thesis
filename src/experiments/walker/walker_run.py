"""在 Walker-delta contact plan 上跑本方法、SR-CGR k=1、k=10（逐包規劃）。

單位：1 包 = 1 單位（文獻為 100 bytes）；速率 400 bps = 0.5 包/秒，傳一包 2 秒。
流量：GS1 → GS2，Nb 包在 [0, 2000) 秒等間隔產生（同文獻）。
Buffer：衛星上限 M 包；地面站不設限（文獻來源 Buffer 無限），以常數負背景占用實作，演算法不變。
"""
import argparse, json, sys, time
sys.path.insert(0, '/home/claude/space-dtn-thesis/src/experiments/dtn_validation')
from fractions import Fraction as Fr
from dtn.model import Contact, Problem, Curve, arrival
from run_performance import plan_one
from dtn import validate as V

RATE_MBPS = {'intra': 25, 'inter': 25, 'gsl': Fr(3, 2)}   # Iridium（ns-2）：ISL 25 Mb/s、上下行 1.5 Mb/s

def load(path, rate, bundle_mb=None):
    d = json.load(open(path)); kinds = d.get('kind')
    def r(i):
        if kinds and bundle_mb: return Fr(RATE_MBPS[kinds[i]]) / (8 * Fr(str(bundle_mb)))   # 包/秒
        return Fr(rate)
    cs = [Contact('c%d' % i, u, v, Fr(a), Fr(b), r(i), Fr(dl).limit_denominator(10**6), ()) for i, (u, v, a, b, dl) in enumerate(d['contacts'])]
    return d['nodes'], cs

def run(cp, nb, M, method, rate=Fr(1, 2), horizon=86400, window=2000, bundle_mb=None, ct=False):
    nodes, cs = load(cp, rate, bundle_mb)
    big = Fr(10**9)
    O = {n: Curve([Fr(0), Fr(horizon)], [-big, -big], [-big, -big]) for n in nodes if n.startswith('GS')}
    P = Problem(cs, None, None, Fr(0), Fr(1), Fr(M), O, Fr(horizon), ct)
    rows, t0 = [], time.perf_counter()
    for i in range(nb):
        g = Fr(window * i, nb)
        Pb = P._replace(src='GS1', dst='GS2', g=g)
        s = time.perf_counter(); sch, why = plan_one(method, Pb); sec = time.perf_counter() - s
        row = {"i": i, "g": float(g), "sec": round(sec, 5), "why": why}
        if sch:
            row.update(arr=float(arrival(Pb, sch)), hops=len(sch), path=">".join(['GS1'] + [c.v for c, _ in sch]))
            P = V.commit(Pb, sch)
        else:
            row.update(arr=None, hops=0, path="")
        rows.append(row)
    return {"cp": cp, "cut_through": ct, "bundle_mb": bundle_mb, "window": window, "Nb": nb, "M": M, "method": method, "wall": round(time.perf_counter() - t0, 2), "rows": rows}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cp"); ap.add_argument("--nb", type=int, nargs="+"); ap.add_argument("--M", type=int, nargs="+")
    ap.add_argument("--methods", nargs="+", default=["ours", "sr1", "sr10"]); ap.add_argument("--out")
    ap.add_argument("--bundle-mb", type=float); ap.add_argument("--window", type=int, default=2000)
    ap.add_argument("--cut-through", action="store_true")
    a = ap.parse_args()
    with open(a.out, "a") as fh:
        for nb in a.nb:
            for M in a.M:
                for me in a.methods:
                    r = run(a.cp, nb, M, me, window=a.window, bundle_mb=a.bundle_mb, ct=a.cut_through); fh.write(json.dumps(r) + "\n"); fh.flush()
                    ok = [x for x in r["rows"] if x["arr"] is not None]
                    dl = sum(x["arr"] - x["g"] for x in ok) / max(1, len(ok))
                    print("%s Nb=%d M=%d %s: delivered %d/%d (%.1f%%) mean delay %.0fs wall %.1fs" % (a.cp.split('/')[-1], nb, M, me, len(ok), nb, 100 * len(ok) / nb, dl, r["wall"]), flush=True)
