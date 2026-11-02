"""規則 2：起送集合的規模診斷。狀態 (contact, s) 已決定 h、A，因此無配額時每條 contact
只需記錄可達起送集合。本程式在 1/16 秒格點上窮舉到目的地出佇列，統計集合可壓成幾段。
只量規模；格點窮舉本身就是答案基準，不能作為區間演算法的正確性證據。"""
import heapq, json, random, sys
from fractions import Fraction as Fr
from cut_through_audit import *

def reach(P):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    pq = [(P.g, 0, P.src, None, None)]; seen = {}; tick = 0; ans = None
    while pq:
        A, _, n, h, cid = heapq.heappop(pq)
        if cid is not None:
            s = h - {c.id: c for c in P.cs}[cid].d
            if s in seen.setdefault(cid, set()): continue
            seen[cid].add(s)
        if n == P.dst: ans = A; break
        for c in out.get(n, []):
            for s in starts(P, c, h, A, True):
                if s in seen.get(c.id, set()): continue
                tick += 1; heapq.heappush(pq, (s + P.S / c.r + c.d, tick, c.v, s + c.d, c.id))
    states = sum(map(len, seen.values())); pieces = 0
    for v in seen.values():
        x = sorted(v); pieces += sum(1 for i, s in enumerate(x) if i == 0 or s - x[i - 1] != GRID)
    return ans, states, pieces, max((len(v) for v in seen.values()), default=0)

P7 = I([mk("ab", "A", "B", 0, 10, r=2), mk("bc", "B", "C", 2, 12, r=2)], "A", "C", Fr(0), Fr(10), Fr(10), {}, Fr(30))
print("B->C opens at 2:", solve(P7, cut=True)[:2], "store:", solve(P7, cut=False)[0])
for hetero in (False, True):
    rng = random.Random(20261102 + hetero); S = PIE = M = N = 0; mx = 0; ok = 0
    for _ in range(1000):
        p = rand(rng, hetero); a, st, pc, m = reach(p); assert a == solve(p, cut=True)[0]
        S += st; PIE += pc; mx = max(mx, pc); ok += a is not None
    print(dict(hetero=hetero, feasible=ok, grid_states=S, interval_pieces=PIE, ratio=round(S / max(PIE, 1), 1), max_pieces_one_instance=mx))
