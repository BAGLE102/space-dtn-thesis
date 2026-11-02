"""Cut-through（收完前可轉發）單包查核，2026-11-02。

所有方法都限制在 1/16 秒格點上，所以「最優」指格點最優，不是連續時間最優。
oracle 狀態為 (node, h, A, 使用次數)；h=首 byte 抵達，A=整包收完。
本包在節點的占用 = 已收 - 已送，依 O_v + 占用 <= M 檢查整次造訪。
範圍：單包；來源、目的地無背景；無配額。非一般證明，非正式路由器。
"""
import argparse, heapq, json, random
from collections import namedtuple
from fractions import Fraction as Fr

C = namedtuple("C", "id u v a b r d F")
I = namedtuple("I", "cs src dst g S M O T")
GRID = Fr(1, 16)
SRC_H = None


def occ(cv, t):
    if not cv or t <= cv[0][0]: return cv[0][1] if cv else Fr(0)
    for (x0, y0), (x1, y1) in zip(cv, cv[1:]):
        if t <= x1: return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
    return cv[-1][1]


def ramp(t, a, b, S):
    if t <= a: return Fr(0)
    if t >= b: return S
    return S * (t - a) / (b - a)


def visit_ok(P, n, h, A, s, f):
    """h is None 代表來源：起始已持有整包。"""
    O = P.O.get(n, [])
    def b(t):
        rec = P.S if h is None else ramp(t, h, A, P.S)
        return rec - ramp(t, s, f, P.S)
    start = A if h is None else h
    pts = {start, A, s, f} | {x for x, _ in O if start < x < f}
    return all(occ(O, t) + b(t) <= P.M for t in pts if t >= start)


def starts(P, c, h, A, cut):
    d = P.S / c.r
    lo = max(c.a, (max(h if h is not None else A, A - d) if cut else A))
    n = (lo / GRID).__ceil__()
    s = Fr(n) * GRID
    out = []
    while s + d <= c.b and s + d + c.d <= P.T:
        if not any(s < y and x < s + d for x, y in c.F) and visit_ok(P, c.u, h, A, s, s + d):
            out.append(s)
        s += GRID
    return out


def solve(P, cut=True, simple=False, select="all", dom="none"):
    """select: all / first_run / first_run_recv。dom: none / min_A / pareto / safe。"""
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    pq = [(P.g, 0, P.src, None, (P.src,), ())]; tick = 0; seen = set(); kept = {}; made = 0
    while pq:
        A, _, n, h, vis, sch = heapq.heappop(pq)
        key = (n, h, A, vis if simple else None)
        if key in seen: continue
        seen.add(key)
        if n == P.dst: return A, sch, made
        if dom != "none" and any(dominated(P, n, x, (h, A), dom) for x in kept.get(n, [])): continue
        kept.setdefault(n, []).append((h, A))
        for c in out.get(n, []):
            if simple and c.v in vis: continue
            ss = starts(P, c, h, A, cut)
            if select != "all":
                if select == "first_run_recv": ss = [s for s in ss if recv_ok(P, c, s)]
                if select == "first_run_lookahead": ss = [s for s in ss if viable(P, c, s, out, cut)]
                ss = [s for i, s in enumerate(ss) if i == 0 or s - ss[i - 1] != GRID]
            d = P.S / c.r
            for s in ss:
                h2, A2 = s + c.d, s + d + c.d
                tick += 1; made += 1
                heapq.heappush(pq, (A2, tick, c.v, h2, vis + (c.v,) if simple else (), sch + ((c.id, s),)))
    return None, (), made


def viable(P, c, s, out, cut):
    """一步前瞻：這次接收至少能接上一個下一跳，或已到目的地。"""
    if c.v == P.dst: return True
    d = P.S / c.r; h, A = s + c.d, s + d + c.d
    return any(starts(P, c2, h, A, cut) for c2 in out.get(c.v, []))


def recv_ok(P, c, s):
    d = P.S / c.r; h = s + c.d; A = h + d; O = P.O.get(c.v, [])
    return all(occ(O, t) + ramp(t, h, A, P.S) <= P.M for t in {h, A} | {x for x, _ in O if h < x < A})


def dominated(P, n, old, new, dom):
    h1, A1 = old; h2, A2 = new
    if h1 is None or h2 is None: return False
    if dom == "min_A": return A1 <= A2
    if h1 > h2 or A1 > A2: return False
    if dom == "pareto": return True
    O = P.O.get(n, [])
    return all(occ(O, t) + P.S <= P.M for t in {h1, A2} | {x for x, _ in O if h1 < x < A2})


def validate(P, sch, cut):
    by = {c.id: c for c in P.cs}; n = P.src; h = None; A = P.g
    for cid, s in sch:
        c = by[cid]; d = P.S / c.r
        if c.u != n or s not in starts(P, c, h, A, cut): return False
        h, A, n = s + c.d, s + d + c.d, c.v
    return n == P.dst


def trap(t0, size, hold, rate=Fr(4)):
    r = size / rate
    return [(t0, Fr(0)), (t0 + r, size), (t0 + r + hold, size), (t0 + 2 * r + hold, Fr(0))]


def add(cvs):
    ts = sorted({t for c in cvs for t, _ in c})
    return [(t, sum(occ(c, t) for c in cvs)) for t in ts]


def mk(id, u, v, a, b, d=0, r=4, F=()):
    return C(id, u, v, Fr(a), Fr(b), Fr(r), Fr(d), tuple((Fr(x), Fr(y)) for x, y in F))


def fixtures():
    bo = [(Fr(2), Fr(0)), (Fr(3), Fr(4)), (Fr(6), Fr(4)), (Fr(7), Fr(0))]
    # PPT 第二包；c1、c2 已用完，c7 依原案例配額不足，故移除。
    ppt = I([mk("c3", "A", "B", 1, 2), mk("c4", "A", "B", 7, 9), mk("c5", "B", "D", 10, 11, 1),
             mk("c6", "A", "C", 1, 2, 1), mk("c8", "C", "D", 2, 3)], "A", "D", Fr(1), Fr(4), Fr(4), {"B": bo}, Fr(16))
    # 速率不同：L1 慢收 h=0,A=10；L2 快收 h=5,A=6（S=4）。
    def par(out_r, b):
        return I([mk("slow", "S", "V", 0, 10, r=Fr(2, 5)), mk("fast", "S", "V", 5, 6, r=4), mk("out", "V", "T", 0, b, r=out_r)],
                 "S", "T", Fr(0), Fr(4), Fr(8), {}, Fr(30))
    # 滿載節點 V 只能同步穿過。
    full = I([mk("in", "S", "V", 2, 3), mk("out", "V", "T", 2, 3)], "S", "T", Fr(0), Fr(4), Fr(4), {"V": [(Fr(0), Fr(4)), (Fr(20), Fr(4))]}, Fr(30))
    # 只有晚起送可行：V 在 2 秒前滿載，in 很早開放；最早區段點 s=0 會失敗。
    late = I([mk("in", "S", "V", 0, 6), mk("out", "V", "T", 2, 3)], "S", "T", Fr(0), Fr(4), Fr(4), {"V": [(Fr(0), Fr(4)), (Fr(1), Fr(4)), (Fr(2), Fr(0))]}, Fr(30))
    wk = I([mk("a", "S", "U", 0, 1), mk("b", "U", "V", 1, 2), mk("c", "V", "U", 5, 6), mk("e", "U", "T", 7, 8)], "S", "T", Fr(0), Fr(4), Fr(4),
           {"U": [(Fr(2), Fr(0)), (Fr(3), Fr(4)), (Fr(4), Fr(4)), (Fr(5), Fr(0))]}, Fr(18))
    return dict(ppt_second=ppt, pareto_out_fast=par(4, 40), pareto_out_slow=par(Fr(4, 9), 40), full_node=full, late_only=late, walk_v5=wk)


def run_fixture(P):
    r = {}
    for name, kw in dict(store=dict(cut=False), cut=dict(cut=True), cut_simple=dict(cut=True, simple=True), first_run=dict(select="first_run"),
                         first_run_recv=dict(select="first_run_recv"), lookahead=dict(select="first_run_lookahead"), lookahead_safe=dict(select="first_run_lookahead", dom="safe"), min_A=dict(dom="min_A"), pareto=dict(dom="pareto"), safe=dict(dom="safe")).items():
        a, s, _ = solve(P, **kw)
        r[name] = None if a is None else str(a)
        if name == "cut": r["cut_schedule"] = [(k, str(v)) for k, v in s]
    return r


def rand(rng, hetero):
    N = ["S", "U", "V", "W", "T"]; cs = []
    for i in range(rng.randint(5, 9)):
        u = rng.choice(N[:4]); v = rng.choice([n for n in N[1:] if n != u])
        a = Fr(rng.randint(0, 20), 2); ln = Fr(rng.randint(2, 8), 2)
        F = ()
        if rng.random() < .2:
            x = a + Fr(rng.randint(0, 4), 2); F = ((x, x + Fr(rng.randint(1, 3), 4)),)
        cs.append(C(f"c{i}", u, v, a, a + ln, Fr(rng.choice([2, 4, 8]) if hetero else 4), Fr(rng.choice([0, 0, 1, 2, 4]), 4), F))
    S = Fr(rng.choice([2, 4])); M = Fr(rng.choice([4, 6]))
    O = {}
    for n in N[1:4]:
        cv = [trap(Fr(rng.randint(0, 24), 2), Fr(rng.choice([1, 2, 3, 4])), Fr(rng.randint(0, 6), 2)) for _ in range(rng.randint(0, 2))]
        if cv: O[n] = add(cv)
    return I(cs, "S", "T", Fr(0), S, M, O, Fr(18))


RULES = dict(first_run=dict(select="first_run"), first_run_recv=dict(select="first_run_recv"), lookahead=dict(select="first_run_lookahead"), lookahead_safe=dict(select="first_run_lookahead", dom="safe"), min_A=dict(dom="min_A"), pareto=dict(dom="pareto"), safe=dict(dom="safe"))


def fuzz(n, seed, hetero):
    rng = random.Random(seed)
    R = dict(n=n, hetero=hetero, cut_feasible=0, store_feasible=0, cut_earlier=0, cut_rescued=0, walk_needed_infeasible=0, walk_earlier=0, invalid=0,
             rules={k: dict(mismatch=0, false_infeasible=0, later=0, wrong_better=0) for k in RULES})
    fails = {}
    for i in range(n):
        P = rand(rng, hetero)
        a, s, _ = solve(P, cut=True); st, _, _ = solve(P, cut=False); sm, _, _ = solve(P, cut=True, simple=True)
        R["cut_feasible"] += a is not None; R["store_feasible"] += st is not None
        if a is not None and st is None: R["cut_rescued"] += 1
        if a is not None and st is not None and a < st: R["cut_earlier"] += 1
        if a is not None and sm is None: R["walk_needed_infeasible"] += 1
        if a is not None and sm is not None and a < sm: R["walk_earlier"] += 1
        if s and not validate(P, s, True): R["invalid"] += 1
        for k, kw in RULES.items():
            x, _, _ = solve(P, **kw); r = R["rules"][k]
            if x != a:
                r["mismatch"] += 1
                if x is None: r["false_infeasible"] += 1
                elif a is None or x < a: r["wrong_better"] += 1
                else: r["later"] += 1
                fails.setdefault(k, dict(i=i, truth=str(a), got=str(x)))
    R["first_fail"] = fails
    return R


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=600); ap.add_argument("--seed", type=int, default=20261102); ap.add_argument("--out", default="cut_through_results.json")
    a = ap.parse_args()
    res = dict(fixtures={k: run_fixture(v) for k, v in fixtures().items()}, equal_rate=fuzz(a.n, a.seed, False), hetero_rate=fuzz(a.n, a.seed + 1, True))
    json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=1)
    for k, v in res["fixtures"].items(): print(k, v)
    print(res["equal_rate"]); print(res["hetero_rate"])
