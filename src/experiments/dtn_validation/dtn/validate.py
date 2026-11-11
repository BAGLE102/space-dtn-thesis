"""限制的定義：回放檢查與提交。不呼叫任何搜尋或篩選函式。

P.ct 為 True 時中繼可 cut-through：s2 ≥ max(h, A − S/r2)；否則收完才送 s2 ≥ A。

占用檢查取停留期間的上確界。資料在整包收完的瞬間 A 交付並離開目的地。
"""
from fractions import Fraction as Fr
from .model import Curve, ramp


def stay_ok(O, M, start, end, own, own_end, pts=()):
    """檢查 start 到 end 的 O(t) + own(t) ≤ M。own_end 是 end 的左極限。"""
    v = own(start)
    if v > 0 and O.right(start) + v > M:
        return False
    if own_end > 0 and O.left(end) + own_end > M:
        return False
    for t in list(pts) + O.between(start, end):
        if start < t < end:
            v = own(t)
            if v > 0 and O.top(t) + v > M:
                return False
    return True


def source_ok(P, c, s):
    d = P.S / c.r
    f = s + d
    own = lambda t: P.S - ramp(t, s, f, P.S)
    return stay_ok(P.O.get(P.src, Curve()), P.M, P.g, f, own, Fr(0), [s])


def relay_ok(P, c1, s1, c2, s2):
    d1, d2 = P.S / c1.r, P.S / c2.r
    h = s1 + c1.d
    A = h + d1
    f = s2 + d2
    if P.ct:
        if s2 < h or f < A:          # cut-through：已開始收，且送不能比收快
            return False
    elif s2 < A:                     # store-and-forward：收完才送
        return False
    own = lambda t: ramp(t, h, A, P.S) - ramp(t, s2, f, P.S)
    return stay_ok(P.O.get(c1.v, Curve()), P.M, h, f, own, Fr(0), [A, s2])


def destination_ok(P, c, s):
    d = P.S / c.r
    h = s + c.d
    A = h + d
    own = lambda t: ramp(t, h, A, P.S)
    return stay_ok(P.O.get(P.dst, Curve()), P.M, h, A, own, P.S)


def hop_ok(P, c, s):
    d = P.S / c.r
    if s < c.a or s + d > c.b or s + d + c.d > P.T:
        return False
    return not any(s < y and x < s + d for x, y in c.F)


def validate(P, sch):
    """獨立檢查整條排程。"""
    if not sch or sch[0][0].u != P.src or sch[-1][0].v != P.dst or sch[0][1] < P.g:
        return False
    for (a, _), (b, _) in zip(sch, sch[1:]):
        if a.v != b.u:
            return False
    if not all(hop_ok(P, c, s) for c, s in sch):
        return False
    if not source_ok(P, *sch[0]) or not destination_ok(P, *sch[-1]):
        return False
    return all(relay_ok(P, c1, s1, c2, s2) for (c1, s1), (c2, s2) in zip(sch, sch[1:]))


def commit(P, sch):
    """寫入預約與占用：來源、中間節點、目的地都納入。"""
    F = {c.id: list(c.F) for c in P.cs}
    O = dict(P.O)
    S = P.S

    def put(n, cv):
        O[n] = O[n].add(cv) if n in O else cv

    for c, s in sch:
        F[c.id].append((s, s + S / c.r))
    c0, s0 = sch[0]
    f0 = s0 + S / c0.r
    if P.g < s0:
        put(P.src, Curve([P.g, s0, f0], [Fr(0), S, Fr(0)], [S, S, Fr(0)]))
    else:
        put(P.src, Curve([s0, f0], [Fr(0), Fr(0)], [S, Fr(0)]))
    for (c1, s1), (c2, s2) in zip(sch, sch[1:]):
        h = s1 + c1.d
        A = h + S / c1.r
        f = s2 + S / c2.r
        if P.ct and s2 < A:
            ts = sorted({h, A, s2, f})
            vs = [ramp(x, h, A, S) - ramp(x, s2, f, S) for x in ts]
            put(c1.v, Curve(ts, vs, vs))
        elif A < s2:
            put(c1.v, Curve([h, A, s2, f], [Fr(0), S, S, Fr(0)], [Fr(0), S, S, Fr(0)]))
        else:
            put(c1.v, Curve([h, A, f], [Fr(0), S, Fr(0)], [Fr(0), S, Fr(0)]))
    c, s = sch[-1]
    h = s + c.d
    A = h + S / c.r
    put(P.dst, Curve([h, A], [Fr(0), S], [Fr(0), Fr(0)]))
    return P._replace(cs=[c._replace(F=tuple(F[c.id])) for c in P.cs], O=O)
