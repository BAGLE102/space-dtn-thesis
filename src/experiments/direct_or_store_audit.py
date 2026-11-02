"""「能直接轉就直接轉，要等就收完才轉」查核，2026-11-02。
每跳二選一：直接轉 s=h（需 r_out<=r_in），或收完才轉 s>=A。限 1/16 秒格點；單包、無配額、
來源與目的地無背景。candidate 把連續直接轉的 contacts 當成一段直通段，只留
（節點，可持有時段）最早 Label。非證明。
"""
import heapq, json, random, sys
from fractions import Fraction as Fr
from cut_through_audit import *

def truth(P):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    pq = [(P.g, 0, P.src, None, None, (), ())]; seen = set(); tick = 0
    while pq:
        A, _, n, h, rin, sch, _x = heapq.heappop(pq)
        if (n, h, A, rin) in seen: continue
        seen.add((n, h, A, rin))
        if n == P.dst: return A, sch
        for c in out.get(n, []):
            d = P.S / c.r; opts = []
            if h is not None and c.r <= rin and c.a <= h and h + d <= c.b and h + d + c.d <= P.T \
               and not any(h < y and x < h + d for x, y in c.F) and visit_ok(P, n, h, A, h, h + d):
                opts.append(h)
            opts += starts(P, c, h, A, False)
            for s in sorted(set(opts)):
                tick += 1
                heapq.heappush(pq, (s + d + c.d, tick, c.v, s + c.d, c.r, sch + ((c.id, s),), ()))
    return None, ()

def holds(P, n):
    O = P.O.get(n, [])
    return lambda a, b: all(occ(O, t) + P.S <= P.M for t in {a, b} | {x for x, _ in O if a < x < b})

def chain_ok(P, ch, A0, s):
    """ch 從節點 u 以 s 起送、其後每跳 s=h。"""
    if s < A0: return None
    h = None; A = A0; n = ch[0].u; cur = s; hs = []
    for i, c in enumerate(ch):
        d = P.S / c.r
        if cur < c.a or cur + d > c.b or cur + d + c.d > P.T or any(cur < y and x < cur + d for x, y in c.F): return None
        if not visit_ok(P, n, h, A, cur, cur + d): return None
        hs.append((c.id, cur)); h = cur + c.d; A = h + d; n = c.v; cur = h
    if n != P.dst:
        c = ch[-1]; O = P.O.get(n, [])
        if not all(occ(O, t) + ramp(t, h, A, P.S) <= P.M for t in {h, A} | {x for x, _ in O if h < x < A}): return None
    return A, tuple(hs), n

def chains(P, out, c0):
    st = [(c0,)]
    while st:
        ch = st.pop(); yield ch
        if ch[-1].v == P.dst: continue
        for c in out.get(ch[-1].v, []):
            if c not in ch and c.r <= ch[-1].r: st.append(ch + (c,))

def cand(P, single=True):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    pq = [(P.g, 0, P.src, ())]; tick = 0; best = {}; made = 0
    while pq:
        A, _, n, sch = heapq.heappop(pq)
        if n == P.dst: return A, sch, made
        if single:
            hk = holds(P, n)
            if n != P.src and any(a <= A and hk(a, A) for a in best.get(n, [])): continue
            best.setdefault(n, []).append(A)
        for c in out.get(n, []):
            for ch in chains(P, out, c):
                d = P.S / c.r; s = max(A, c.a); s = Fr((s / GRID).__ceil__()) * GRID; prev = False
                while s + d <= c.b:
                    r = chain_ok(P, ch, A, s)
                    if r and not prev:
                        tick += 1; made += 1
                        heapq.heappush(pq, (r[0], tick, r[2], sch + r[1]))
                    prev = bool(r); s += GRID
    return None, (), made

def run(n, seed, hetero):
    rng = random.Random(seed); R = dict(n=n, hetero=hetero, feasible=0, mismatch=0, later=0, false_inf=0, wrong=0, labels_max=0, ex=None)
    for i in range(n):
        P = rand(rng, hetero); t, _ = truth(P); c, s, m = cand(P)
        R["feasible"] += t is not None; R["labels_max"] = max(R["labels_max"], m)
        if c != t:
            R["mismatch"] += 1
            if c is None: R["false_inf"] += 1
            elif t is None or c < t: R["wrong"] += 1
            else: R["later"] += 1
            if not R["ex"]: R["ex"] = dict(i=i, truth=str(t), cand=str(c), sch=[(a, str(b)) for a, b in s])
    return R

if __name__ == "__main__":
    n = int(sys.argv[1]); fx = {}
    for k, P in fixtures().items():
        t, _ = truth(P); c, s, _m = cand(P); fx[k] = dict(truth=str(t), cand=str(c), sch=[(a, str(b)) for a, b in s])
    res = dict(fixtures=fx, equal=run(n, 20261102, False), hetero=run(n, 20261103, True))
    json.dump(res, open("direct_or_store_results.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=0))
