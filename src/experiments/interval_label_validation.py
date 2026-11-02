"""區間 Label 候選方法驗證（RELAX 模式），2026-11-02。

精確有理數；不靠格點產生區間。範圍：無配額；來源、目的地無背景；背景為連續曲線；
全部節點可邊收邊轉。TRACK 未實作，只統計 RELAX 結果是否自我重疊。
oracle 限格點，因此只能檢查：候選不應晚於格點最優，且候選排程須通過獨立重放。
"""
import argparse, heapq, json, random
from fractions import Fraction as Fr
import cut_through_audit as ct
from cut_through_audit import C, I, occ, ramp, trap, add, mk, rand, fixtures


def visit(P, n, h, A, s, f):
    O = P.O.get(n, []); S = P.S
    st = A if h is None else h
    pts = {st, A, s, f} | {x for x, _ in O if st < x < f}
    for t in pts:
        if t < st: continue
        rec = S if h is None else ramp(t, h, A, S)
        if occ(O, t) + rec - ramp(t, s, f, S) > P.M: return False
    return True


def subtract_open(parts, x, y):
    out = []
    for l, r in parts:
        if r <= x or l >= y:
            out.append((l, r)); continue
        if l <= x: out.append((l, x))
        if r >= y: out.append((y, r))
    return out


def start_parts(P, c, head):
    d = P.S / c.r; lo = max(c.a, head); hi = min(c.b - d, P.T - d - c.d)
    if lo > hi: return []
    p = [(lo, hi)]
    for x, y in c.F: p = subtract_open(p, x - d, y)
    return p


def star(I1, U, late=True):
    if late:
        v = None
        for l, r in I1:
            if l <= U: v = min(r, U)
        return v
    return I1[0][0] if I1 and I1[0][0] <= U else None


class Stat: opens = 0


def buffer_filter(P, parts, I1, c1, c2, late=True):
    n = c1.v; S = P.S; d1, d2 = S / c1.r, S / c2.r; dl = c1.d; ex = max(Fr(0), d1 - d2); O = P.O.get(n, [])
    U = lambda s: s - dl - ex
    def feas(s):
        k = star(I1, U(s), late)
        if k is None: return False
        h = k + dl
        return visit(P, n, h, h + d1, s, s + d2)
    res = []
    verts = [x for x, _ in O]
    for lo, hi in parts:
        if lo == hi:
            if feas(lo): res.append((lo, hi))
            continue
        cr = {lo, hi}
        for l, r in I1:
            cr |= {l + dl + ex, r + dl + ex}
        cr = sorted(x for x in cr if lo <= x <= hi)
        pts = set(cr)
        for p, q in zip(cr, cr[1:]):
            a, b = p + (q - p) / 3, p + 2 * (q - p) / 3
            ka, kb = star(I1, U(a), late), star(I1, U(b), late)
            if ka is None or kb is None: continue
            al = (kb - ka) / (b - a); be = ka - al * a
            mv = [(al, be + dl), (al, be + dl + d1), (Fr(1), Fr(0)), (Fr(1), d2)]
            sub = {p, q}
            for i, (a1, b1) in enumerate(mv):
                for x in verts:
                    if a1 != 0:
                        z = (x - b1) / a1
                        if p < z < q: sub.add(z)
                for a2, b2 in mv[i + 1:]:
                    if a1 != a2:
                        z = (b2 - b1) / (a1 - a2)
                        if p < z < q: sub.add(z)
            sub = sorted(sub); pts |= set(sub)
            for u, w in zip(sub, sub[1:]):
                e, g = u + (w - u) / 3, u + 2 * (w - u) / 3
                def occs(s):
                    k = al * s + be; h = k + dl; A = h + d1; f = s + d2
                    ts = [h, A, s, f]
                    m = (u + w) / 2; km = al * m + be; lo_t = km + dl; hi_t = m + d2
                    ts += [x for x in verts if lo_t < x < hi_t]
                    return [occ(O, t) + ramp(t, h, A, S) - ramp(t, s, f, S) - P.M for t in ts]
                for fa, fb in zip(occs(e), occs(g)):
                    if fa != fb:
                        z = e + (0 - fa) * (g - e) / (fb - fa)
                        if u < z < w: pts.add(z)
        pts = sorted(pts); cur = None
        for i, p in enumerate(pts):
            ok = feas(p)
            if ok:
                if cur is None: cur = [p, p]
                else: cur[1] = p
            else:
                if cur: res.append(tuple(cur)); cur = None
            if i + 1 < len(pts):
                m = (p + pts[i + 1]) / 2
                if feas(m):
                    if not ok: Stat.opens += 1
                    if cur is None: cur = [p if ok else m, p if ok else m]
                    if not feas(pts[i + 1]): Stat.opens += 1
                    cur[1] = m
                elif cur:
                    res.append(tuple(cur)); cur = None
        if cur: res.append(tuple(cur))
    # 合併相接段
    res.sort(); out = []
    for l, r in res:
        if out and l <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], r))
        else: out.append((l, r))
    return out


def minus(parts, done):
    for l, r in done:
        new = []
        for a, b in parts:
            if b < l or a > r: new.append((a, b)); continue
            if a < l: new.append((a, l))   # 左端 l 已到過；存成閉區間只會重複一個點
            if b > r: new.append((r, b))
        parts = new
    return [(a, b) for a, b in parts if a < b or not any(l <= a <= r for l, r in done)]


class L:
    __slots__ = ("c", "I", "pred", "key")
    def __init__(s, c, I, pred, key): s.c, s.I, s.pred, s.key = c, I, pred, key


def search(P, closure=False, late=True):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    Q = []; tick = 0; reached = {c.id: [] for c in P.cs}; made = pops = 0; maxp = 0
    def insert(c, parts, pred):
        nonlocal tick, made
        new = minus(parts, reached[c.id])
        reached[c.id] = merge(reached[c.id] + new)
        for I_ in new:
            k = I_[0] + P.S / c.r + c.d; tick += 1; made += 1
            heapq.heappush(Q, (k, tick, L(c, [I_], pred, k)))
    for c in out.get(P.src, []):
        insert(c, start_parts(P, c, P.g), None)
    goal = None
    while Q:
        k, _, l = heapq.heappop(Q); pops += 1
        if l.c.v == P.dst:
            if goal is None: goal = l
            if not closure: break
            continue
        c1 = l.c; d1 = P.S / c1.r
        for c2 in out.get(c1.v, []):
            d2 = P.S / c2.r
            head = l.I[0][0] + c1.d + max(Fr(0), d1 - d2)
            parts = start_parts(P, c2, head)
            insert(c2, buffer_filter(P, parts, l.I, c1, c2, late), l)
    maxp = max((len(v) for v in reached.values()), default=0)
    return goal, reached, dict(labels=made, pops=pops, max_parts=maxp)


def merge(p):
    p = sorted(p); o = []
    for l, r in p:
        if o and l <= o[-1][1]: o[-1] = (o[-1][0], max(o[-1][1], r))
        else: o.append((l, r))
    return o


def backtrack(P, goal):
    l = goal; s = l.I[0][0]; sch = [(l.c, s)]
    while l.pred is not None:
        q = l.pred; d = P.S / q.c.r; dn = P.S / l.c.r
        k = star(q.I, s - q.c.d - max(Fr(0), d - dn), True)
        sch.insert(0, (q.c, k)); l = q; s = k
    return sch


def replay(P, sch):
    """獨立重放：不呼叫搜尋或篩選函式。"""
    if sch[0][0].u != P.src or sch[-1][0].v != P.dst: return False
    prev = None; n = P.src
    for c, s in sch:
        d = P.S / c.r; f = s + d
        if c.u != n or s < c.a or f > c.b or f + c.d > P.T: return False
        if any(s < y and x < f for x, y in c.F): return False
        if prev is None:
            if s < P.g: return False
            h, A = None, P.g
        else:
            h = prev[1] + prev[0].d; A = h + P.S / prev[0].r
            if s < h or f < A: return False
        O = P.O.get(n, [])
        st = P.g if h is None else h
        for t in {st, A, s, f} | {x for x, _ in O if st < x < f}:
            if t < st: continue
            rec = P.S if h is None else (Fr(0) if t <= h else P.S if t >= A else P.S * (t - h) / (A - h))
            sent = Fr(0) if t <= s else P.S if t >= f else P.S * (t - s) / d
            if occ(O, t) + rec - sent > P.M: return False
        prev = (c, s); n = c.v
    c, s = sch[-1]
    return True


def overlap(P, sch):
    v = []; n = P.src; prevf = None
    last = {}
    for c, s in sch:
        d = P.S / c.r; f = s + d; h = s + c.d
        last[c.u] = f
        if c.v in last and h < last[c.v]: return True
    return False


def commit(P, sch):
    F = {c.id: list(c.F) for c in P.cs}; O = {k: list(v) for k, v in P.O.items()}
    prev = None
    for c, s in sch:
        d = P.S / c.r; f = s + d; F[c.id].append((s, f))
        if prev is not None:
            pc, ps = prev; h = ps + pc.d; A = h + P.S / pc.r; n = c.u
            ts = sorted({h, A, s, f})
            cv = [(t, ramp(t, h, A, P.S) - ramp(t, s, f, P.S)) for t in ts]
            O[n] = add([O[n], cv]) if n in O else cv
        prev = (c, s)
    cs = [c._replace(F=tuple(F[c.id])) for c in P.cs]
    return P._replace(cs=cs, O=O)


def on_grid(reach, g):
    return {s for s in g if any(l <= s <= r for l, r in reach)}


def grid_closure(P):
    out = {}
    for c in P.cs: out.setdefault(c.u, []).append(c)
    R = {c.id: set() for c in P.cs}
    for c in out.get(P.src, []): R[c.id] |= set(ct.starts(P, c, None, P.g, True))
    work = [c for c in P.cs if R[c.id]]
    while work:
        c1 = work.pop()
        if c1.v == P.dst: continue
        d1 = P.S / c1.r
        for c2 in out.get(c1.v, []):
            add_ = set()
            for s1 in list(R[c1.id]):
                h = s1 + c1.d
                add_ |= set(ct.starts(P, c2, h, h + d1, True))
            if not add_ <= R[c2.id]:
                R[c2.id] |= add_; work.append(c2)
    return R


def run(n, seed, hetero, grid, bundles=1):
    ct.GRID = grid
    rng = random.Random(seed)
    R = dict(n=n, hetero=hetero, grid=str(grid), bundles=bundles, queries=0, feasible=0, invalid=0, later_than_grid=0, grid_only=0, earlier_than_grid=0, cand_only=0, overlap=0, max_parts=0, max_labels=0, examples=[])
    for i in range(n):
        P = rand(rng, hetero)
        for b in range(bundles):
            R["queries"] += 1
            g, _, st, = search(P)[0], None, search(P)[2]
            a, gsch, _ = ct.solve(P, cut=True)
            R["max_parts"] = max(R["max_parts"], st["max_parts"]); R["max_labels"] = max(R["max_labels"], st["labels"])
            sch = backtrack(P, g) if g else None
            ga = g.key if g else None
            if ga is not None: R["feasible"] += 1
            if sch and not replay(P, sch):
                R["invalid"] += 1; R["examples"].append(dict(kind="invalid", i=i, b=b))
            if sch and overlap(P, sch): R["overlap"] += 1
            if a is not None and ga is None:
                R["grid_only"] += 1; R["examples"].append(dict(kind="grid_only", i=i, b=b, grid=str(a)))
            elif a is None and ga is not None: R["cand_only"] += 1
            elif a is not None and ga > a:
                R["later_than_grid"] += 1; R["examples"].append(dict(kind="later", i=i, b=b, grid=str(a), cand=str(ga)))
            elif a is not None and ga < a: R["earlier_than_grid"] += 1
            if not sch: break
            if bundles > 1: P = commit(P, sch)
    return R


def reach_test(n, seed, grid):
    ct.GRID = grid; rng = random.Random(seed); R = dict(n=n, grid=str(grid), missing_grid_points=0, extra_grid_points=0, grid_points=0, bad_instances=0)
    for i in range(n):
        P = rand(rng, i % 2 == 1); g = grid_closure(P); _, re, _ = search(P, closure=True); bad = False
        for c in P.cs:
            d = P.S / c.r; pts = []
            x = Fr((c.a / grid).__ceil__()) * grid
            while x + d <= c.b: pts.append(x); x += grid
            cg = on_grid(re[c.id], pts); R["grid_points"] += len(g[c.id])
            m = g[c.id] - cg; e = cg - g[c.id]
            R["missing_grid_points"] += len(m); R["extra_grid_points"] += len(e); bad |= bool(m)
        R["bad_instances"] += bad
    return R


def stress(rng, hetero):
    """Buffer 緊、contact 窗長、背景多，讓邊收邊轉與 buffer 真正互相影響。"""
    N = ["S", "U", "V", "W", "T"]; cs = []
    for i in range(rng.randint(6, 10)):
        u = rng.choice(N[:4]); v = rng.choice([n for n in N[1:] if n != u])
        a = Fr(rng.randint(0, 16), 2); ln = Fr(rng.randint(4, 14), 2)
        F = ()
        if rng.random() < .3:
            x = a + Fr(rng.randint(0, 6), 2); F = ((x, x + Fr(rng.randint(1, 4), 4)),)
        cs.append(C(f"c{i}", u, v, a, a + ln, Fr(rng.choice([2, 4, 8]) if hetero else 4), Fr(rng.choice([0, 0, 1, 2]), 4), F))
    S = Fr(rng.choice([2, 4])); M = S + Fr(rng.choice([0, 0, 1]))
    O = {}
    for n in N[1:4]:
        cv = [trap(Fr(rng.randint(0, 20), 2), Fr(rng.choice([1, 2, 3, 4])), Fr(rng.randint(0, 8), 2)) for _ in range(rng.randint(1, 3))]
        O[n] = add(cv)
    return I(cs, "S", "T", Fr(0), S, M, O, Fr(18))


def run_stress(n, seed, grid, bundles=1):
    ct.GRID = grid; rng = random.Random(seed)
    R = dict(n=n, grid=str(grid), bundles=bundles, queries=0, feasible=0, invalid=0, later_than_grid=0, grid_only=0, earlier_than_grid=0, cand_only=0, overlap=0, max_parts=0, max_labels=0, missing_reach=0, extra_reach=0, reach_points=0, examples=[])
    for i in range(n):
        P = stress(rng, i % 2 == 1)
        for b in range(bundles):
            R["queries"] += 1
            g, re, st = search(P, closure=True); a, _, _ = ct.solve(P, cut=True); gr = grid_closure(P)
            R["max_parts"] = max(R["max_parts"], st["max_parts"]); R["max_labels"] = max(R["max_labels"], st["labels"])
            for c in P.cs:
                d = P.S / c.r; pts = []; x = Fr((c.a / grid).__ceil__()) * grid
                while x + d <= c.b: pts.append(x); x += grid
                cg = on_grid(re[c.id], pts); R["reach_points"] += len(gr[c.id])
                R["missing_reach"] += len(gr[c.id] - cg); R["extra_reach"] += len(cg - gr[c.id])
            sch = backtrack(P, g) if g else None; ga = g.key if g else None
            if ga is not None: R["feasible"] += 1
            if sch and not replay(P, sch): R["invalid"] += 1; R["examples"].append(dict(kind="invalid", i=i, b=b))
            if sch and overlap(P, sch): R["overlap"] += 1
            if a is not None and ga is None: R["grid_only"] += 1; R["examples"].append(dict(kind="grid_only", i=i, b=b, grid=str(a)))
            elif a is None and ga is not None: R["cand_only"] += 1
            elif a is not None and ga > a: R["later_than_grid"] += 1; R["examples"].append(dict(kind="later", i=i, b=b, grid=str(a), cand=str(ga)))
            elif a is not None and ga < a: R["earlier_than_grid"] += 1
            if not sch: break
            if bundles > 1: P = commit(P, sch)
    return R


def control(n, seed, grid):
    """負控制：故意改錯，確認這些測試抓得到。"""
    ct.GRID = grid; rng = random.Random(seed)
    R = dict(n=n, earliest_predecessor_wrong=0, earliest_predecessor_reach_diff=0, concrete_earliest_wrong=0, skip_buffer_invalid=0, no_cut_through_later=0)
    for i in range(n):
        P = stress(rng, i % 2 == 1); a, _, _ = ct.solve(P, cut=True); g, re, _ = search(P, closure=True)
        ge, ree, _ = search(P, closure=True, late=False)
        x = ge.key if ge else None; gk = g.key if g else None
        if x != gk: R["earliest_predecessor_wrong"] += 1
        if ree != re: R["earliest_predecessor_reach_diff"] += 1
        fr, _, _ = ct.solve(P, cut=True, select="first_run")
        if fr != a: R["concrete_earliest_wrong"] += 1
        st, _, _ = ct.solve(P, cut=False)
        if a is not None and (st is None or st > a): R["no_cut_through_later"] += 1
    return R


def fx():
    B7 = [(Fr(0), Fr(7)), (Fr(40), Fr(7))]
    D = {}
    D["7秒案例"] = I([mk("ab", "A", "B", 0, 10, r=2), mk("bc", "B", "C", 2, 12, r=2)], "A", "C", Fr(0), Fr(10), Fr(10), {}, Fr(40))
    D["B只剩3MB"] = I([mk("ab", "A", "B", 0, 10, r=2), mk("bc", "B", "C", 2, 12, r=2)], "A", "C", Fr(0), Fr(10), Fr(10), {"B": B7}, Fr(40))
    D["兩段區間"] = I([mk("ab", "A", "B", 0, 10, r=2), mk("bc", "B", "C", 2, 20, r=2, F=[(9, 10)])], "A", "C", Fr(0), Fr(10), Fr(10), {}, Fr(40))
    D.update(fixtures())
    out = {}
    for k, P in D.items():
        g, re, st = search(P, closure=True); sch = backtrack(P, g) if g else None
        out[k] = dict(arrival=str(g.key) if g else None, schedule=[(c.id, str(s)) for c, s in sch] if sch else None, valid=replay(P, sch) if sch else None,
                      reach={c: [[str(a), str(b)] for a, b in v] for c, v in re.items() if v})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=200); a = ap.parse_args()
    res = dict(fixtures=fx()); g1 = Fr(1, 16); n = a.n
    jobs = [("single_equal", lambda: run(n, 20261102, False, g1)), ("single_hetero", lambda: run(n, 20261103, True, g1)),
            ("multi_equal", lambda: run(n // 2, 20261104, False, g1, 3)), ("multi_hetero", lambda: run(n // 2, 20261105, True, g1, 3)),
            ("reach", lambda: reach_test(n // 2, 20261106, g1)), ("stress_single", lambda: run_stress(n, 20261108, g1)),
            ("stress_multi", lambda: run_stress(n // 2, 20261109, g1, 3)), ("control", lambda: control(n, 20261107, g1)),
            ("stress_fine_grid", lambda: run_stress(max(10, n // 20), 20261110, Fr(1, 48)))]
    for k, f in jobs:
        res[k] = f(); res["open_flags"] = Stat.opens
        json.dump(res, open("interval_label_results.json", "w"), ensure_ascii=False, indent=1)
        print(k, json.dumps(res[k], ensure_ascii=False), flush=True)
