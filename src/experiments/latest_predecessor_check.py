"""查核：對固定 s2，只檢查 R 中「不違反先後條件的最晚 s1」是否等於枚舉 R 中所有 s1。
限 1/16 秒格點；單包、無配額；來源與目的地無背景。"""
import random
from fractions import Fraction as Fr
from cut_through_audit import *

def next_set(P, c1, R, c2, rule):
    d1, d2 = P.S / c1.r, P.S / c2.r; out = set(); s = Fr((c2.a / GRID).__ceil__()) * GRID
    while s + d2 <= c2.b and s + d2 + c2.d <= P.T:
        if not any(s < y and x < s + d2 for x, y in c2.F):
            ub = min(s - c1.d, s + d2 - d1 - c1.d); cand = [x for x in R if x <= ub]
            if rule == "latest": cand = cand[-1:]
            if any(visit_ok(P, c1.v, x + c1.d, x + c1.d + d1, s, s + d2) for x in cand): out.add(s)
        s += GRID
    return out

def closure(P, rule):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    R = {c.id: set() for c in P.cs}; by = {c.id: c for c in P.cs}
    for c in out.get(P.src, []): R[c.id] |= set(starts(P, c, None, P.g, True))
    ch = True
    while ch:
        ch = False
        for c1 in P.cs:
            if c1.v == P.dst or not R[c1.id]: continue
            r = sorted(R[c1.id])
            for c2 in out.get(c1.v, []):
                n = next_set(P, c1, r, c2, rule)
                if not n <= R[c2.id]: R[c2.id] |= n; ch = True
    return R

bad = tot = 0
for hetero in (False, True):
    rng = random.Random(20261102 + hetero)
    for i in range(400):
        P = rand(rng, hetero); tot += 1
        if closure(P, "all") != closure(P, "latest"): bad += 1; print("diff", hetero, i)
print(dict(instances=tot, different=bad))
