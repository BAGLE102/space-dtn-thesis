"""允許重訪、但同一 bundle 不可與自己衝突：比較三種做法。限 1/16 秒格點、單包、無配額。
none=不檢查；exact=新造訪開始時，該節點上一段造訪必須已送完（狀態記未結束造訪）；
chain=狀態只記目前邊收邊轉段經過的節點，收完整包後清空，段內不得回到這些節點。"""
import heapq, random
from fractions import Fraction as Fr
from cut_through_audit import *

def run(P, mode):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    pq = [(P.g, 0, P.src, None, (), ())]; seen = set(); tick = 0; maxh = 0
    while pq:
        A, _, n, h, hist, sch = heapq.heappop(pq)
        k = (n, h, A, hist)
        if k in seen: continue
        seen.add(k); maxh = max(maxh, len(hist))
        if n == P.dst: return A, sch, len(seen), maxh
        for c in out.get(n, []):
            d = P.S / c.r
            for s in starts(P, c, h, A, True):
                f, h2 = s + d, s + c.d
                if mode == "exact":
                    H = tuple(sorted(x for x in hist + ((n, f),) if x[1] > h2))
                    if any(x[0] == c.v for x in H): continue
                elif mode == "chain":
                    H = (tuple(sorted(set(hist) | {n})) if h is not None and s < A else (n,))
                    if c.v in H: continue
                else: H = ()
                tick += 1; heapq.heappush(pq, (h2 + d, tick, c.v, h2, H, sch + ((c.id, s),)))
    return None, (), len(seen), maxh

def nodes(P, s):
    by = {c.id: c for c in P.cs}; return [P.src] + [by[c].v for c, _ in s]

for het in (False, True):
    rng = random.Random(20261102 + het); R = dict(hetero=het, feasible=0, none_vs_exact=0, chain_vs_exact=0, none_schedule_self_conflict=0, states_none=0, states_exact=0, states_chain=0, max_hist_exact=0, max_hist_chain=0)
    for _ in range(1000):
        P = rand(rng, het); a, sa, na, _ = run(P, "none"); b, sb, nb, hb = run(P, "exact"); c, sc, nc, hc = run(P, "chain")
        R["feasible"] += b is not None; R["none_vs_exact"] += a != b; R["chain_vs_exact"] += c != b
        R["states_none"] += na; R["states_exact"] += nb; R["states_chain"] += nc; R["max_hist_exact"] = max(R["max_hist_exact"], hb); R["max_hist_chain"] = max(R["max_hist_chain"], hc)
    print(R)
# 構造案例：短環可能自我重疊
P = I([mk("a", "S", "U", 0, 2), mk("b", "U", "V", 0, 3), mk("c", "V", "U", 0, 3), mk("e", "U", "T", 0, 6)], "S", "T", Fr(0), Fr(4), Fr(4), {}, Fr(18))
print("short cycle", [run(P, m)[:2] for m in ("none", "exact", "chain")])
print("V5", [run(fixtures()["walk_v5"], m)[:2] for m in ("none", "exact", "chain")])
