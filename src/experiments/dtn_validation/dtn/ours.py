"""本方法：區間 Label。對應文件 Algorithm 2~6。

P.ct=False：store-and-forward（收完才送）；P.ct=True：cut-through（邊收邊送，送不能比收快）。
"""
import heapq
from collections import namedtuple
from fractions import Fraction as Fr
from .model import Curve, lag, out_index, ramp
from .validate import destination_ok, relay_ok, source_ok

Label = namedtuple("Label", "c lo hi pred")


def subtract_open(parts, x, y):
    """閉區間集合移除開區間 (x, y)。"""
    out = []
    for a, b in parts:
        if y <= a or x >= b:
            out.append((a, b))
            continue
        if a <= x:
            out.append((a, x))
        if y <= b:
            out.append((y, b))
    return out


def minus(parts, done):
    """閉區間集合移除已到過的部分，done 已排序且不重疊。"""
    out = []
    for a, b in parts:
        cur, closed = a, False
        for x, y in done:
            if y < cur:
                continue
            if x > b:
                break
            if x > cur:
                out.append((cur, x))
            cur, closed = max(cur, y), True
            if cur >= b:
                break
        if cur < b or (cur == b and not closed):
            out.append((cur, b))
    return out


def merge(parts):
    out = []
    for a, b in sorted(parts):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def candidate_range(P, c, head):
    """Algorithm 3：contact 時段、期限、預約。"""
    d = P.S / c.r
    lo, hi = max(c.a, head), min(c.b - d, P.T - d - c.d)
    if lo > hi:
        return []
    parts = [(lo, hi)]
    for x, y in c.F:
        parts = subtract_open(parts, x - d, y)
    return parts


def solve_region(P, lo, hi, bps, feas, vals):
    """在 [lo, hi] 找出全部可行時間。

    bps 切開後，每一小段內 vals 的每個值都是線性的，可直接解不等式。
    """
    pts = sorted({lo, hi} | {b for b in bps if lo < b < hi})
    res = [(p, p) for p in pts if feas(p)]
    for p, q in zip(pts, pts[1:]):
        e, g, m = p + (q - p) / 3, p + 2 * (q - p) / 3, (p + q) / 2
        L, H, ok = p, q, True
        for va, vb in zip(vals(e, m), vals(g, m)):
            k = (vb - va) / (g - e)
            if k == 0:
                if va > P.M:
                    ok = False
                    break
            elif k > 0:
                H = min(H, e + (P.M - va) / k)
            else:
                L = max(L, e + (P.M - va) / k)
        if ok and L <= H:
            res.append((L, H))
    return merge(res)


def source_filter(P, c, parts):
    """SourceBufferFilter：來源從 g 起持有整包，邊送邊釋放。"""
    O = P.O.get(P.src, Curve())
    d = P.S / c.r
    out = []
    for lo, hi in parts:
        if O.peak(P.g, hi + d) + P.S <= P.M:
            out.append((lo, hi))
            continue
        verts = O.between(P.g, hi + d)

        def vals(s, m):
            res = [O.right(P.g) + P.S, O.top(s) + P.S]
            for x in O.between(P.g, m + d):
                res.append(O.top(x) + P.S - ramp(x, s, s + d, P.S))
            return res

        bps = [x for x in verts] + [x - d for x in verts]
        out += solve_region(P, lo, hi, bps, lambda s: source_ok(P, c, s), vals)
    return out


def destination_filter(P, c, parts):
    """DestinationFilter：目的地只收不送，整包收完時交付。"""
    O = P.O.get(P.dst, Curve())
    if not O.ts:
        return parts if P.S <= P.M else []
    d = P.S / c.r
    out = []
    for lo, hi in parts:
        if O.peak(lo + c.d, hi + c.d + d) + P.S <= P.M:
            out.append((lo, hi))
            continue
        verts = O.between(lo + c.d, hi + c.d + d)

        def vals(s, m):
            h, A = s + c.d, s + c.d + d
            res = [O.left(A) + P.S]
            for x in O.between(m + c.d, m + c.d + d):
                res.append(O.top(x) + ramp(x, h, A, P.S))
            return res

        bps = [x - c.d for x in verts] + [x - c.d - d for x in verts]
        out += solve_region(P, lo, hi, bps, lambda s: destination_ok(P, c, s), vals)
    return out


def buffer_filter(P, parts, L1, c2):
    """Algorithm 4：中間節點 buffer。每個 s2 只測最晚的 s1*。

    s1* = min(L1.hi, s2 − dl − lag)；store-and-forward 時 lag = S/r1，
    cut-through 時 lag = max(0, S/r1 − S/r2)。
    """
    c1 = L1.c
    n = c1.v
    O = P.O.get(n, Curve())
    d1, d2, dl = P.S / c1.r, P.S / c2.r, c1.d
    gap = lag(P, c1, c2)
    clamp = L1.hi + dl + gap
    out = []

    def star(s):
        u = s - dl - gap
        return None if u < L1.lo else min(L1.hi, u)

    def feas(s):
        k = star(s)
        return k is not None and relay_ok(P, c1, k, c2, s)

    for lo, hi in parts:
        if O.peak(L1.lo + dl, hi + d2) + P.S <= P.M:
            out.append((lo, hi))
            continue

        def vals(s, m):
            k = star(s)
            h, A, f = k + dl, k + dl + d1, s + d2
            own = lambda x: ramp(x, h, A, P.S) - ramp(x, s, f, P.S)
            hm = star(m) + dl
            res = [O.top(A) + own(A), O.top(s) + own(s)]
            for x in O.between(hm, m + d2):
                res.append(O.top(x) + own(x))
            return res

        verts = O.between(L1.lo + dl, hi + d2)
        # 新包的轉折 h = s − gap、A = s − gap + d1、s、f = s + d2 碰到 O 的變化點 x
        # clamp 之後 h、A 固定；cut-through 時 s 越過固定的 A，own(A)、own(s) 會折彎
        bps = [clamp, L1.hi + dl + d1]
        for x in verts:
            bps += [x, x - d2, x + gap, x + gap - d1]
        out += solve_region(P, lo, hi, bps, feas, vals)
    return merge(out)


def search(P):
    """Algorithm 2。回傳到目的地的 Label，找不到回傳 None。"""
    out = out_index(P.cs)
    Q, tick, reached = [], 0, {}

    def insert(c, parts, pred):
        nonlocal tick
        done = reached.get(c.id, [])
        new = merge(minus(parts, done))
        if not new:
            return
        reached[c.id] = merge(done + new)
        for a, b in new:
            tick += 1
            heapq.heappush(Q, (a + P.S / c.r + c.d, tick, Label(c, a, b, pred)))

    if P.S > P.M:
        return None
    for c in out.get(P.src, []):
        parts = source_filter(P, c, candidate_range(P, c, P.g))
        if c.v == P.dst:
            parts = destination_filter(P, c, parts)
        insert(c, parts, None)
    while Q:
        _, _, L1 = heapq.heappop(Q)
        if L1.c.v == P.dst:
            return L1
        for c2 in out.get(L1.c.v, []):
            head = L1.lo + L1.c.d + lag(P, L1.c, c2)
            parts = candidate_range(P, c2, head)
            if not parts:
                continue
            parts = buffer_filter(P, parts, L1, c2)
            if c2.v == P.dst:
                parts = destination_filter(P, c2, parts)
            insert(c2, parts, L1)
    return None


def backtrack(P, goal):
    """Algorithm 6：最後一跳取最早，往前每跳取不超過上限的最大值。"""
    L, s = goal, goal.lo
    sch = [(L.c, s)]
    while L.pred is not None:
        q = L.pred
        k = min(q.hi, s - q.c.d - lag(P, q.c, L.c))
        sch.insert(0, (q.c, k))
        L, s = q, k
    return sch


def plan(P):
    goal = search(P)
    return backtrack(P, goal) if goal else None
