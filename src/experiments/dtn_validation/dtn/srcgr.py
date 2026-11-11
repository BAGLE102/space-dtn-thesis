"""對照組：簡化版 SR-CGR。

來源算完整路徑、簡單路徑、每跳盡早送、選路不看 buffer。
轉送模型跟隨 P.ct：False 收完才轉；True 可 cut-through（與本方法相同規則）。
k=1 為 sr1；k=10 為 sr10（Yen k 條，依序取第一條通過回放者）。
這不是完整 CGR：沒有實際運作時的逐跳重算。
"""
import heapq
from .model import lag, out_index
from .validate import validate


def fit(c, t, d):
    s = max(c.a, t)
    for x, y in sorted(c.F):
        if s + d <= x:
            break
        if s < y:
            s = y
    return s if s + d <= c.b else None


def dijkstra(P, out, start, t0, ban_c, ban_n, prev=None):
    """prev=(contact, s)：spur 起點前一跳，用來算 cut-through 的最早起送。"""
    pq, best, tick = [], set(), 0
    for c in out.get(start, []):
        if c.id in ban_c or c.v in ban_n:
            continue
        d = P.S / c.r
        t = prev[1] + prev[0].d + lag(P, prev[0], c) if prev else t0
        s = fit(c, t, d)
        if s is None or s + d + c.d > P.T:
            continue
        tick += 1
        heapq.heappush(pq, (s + d + c.d, tick, c, s, None))
    while pq:
        A, _, c, s, prev = heapq.heappop(pq)
        if c.id in best:
            continue
        node = (c, s, prev)
        best.add(c.id)
        if c.v == P.dst:
            route, n = [], node
            while n:
                route.insert(0, (n[0], n[1]))
                n = n[2]
            return A, route
        seen, n = {start} | set(ban_n), node
        while n:
            seen.add(n[0].v)
            n = n[2]
        for c2 in out.get(c.v, []):
            if c2.b < A or c2.v in seen or c2.id in ban_c or c2.id in best:
                continue
            d = P.S / c2.r
            s2 = fit(c2, s + c.d + lag(P, c, c2), d)
            if s2 is None or s2 + d + c2.d > P.T:
                continue
            tick += 1
            heapq.heappush(pq, (s2 + d + c2.d, tick, c2, s2, node))
    return None


def reschedule(P, contacts):
    r = []
    for c in contacts:
        d = P.S / c.r
        t = r[-1][1] + r[-1][0].d + lag(P, r[-1][0], c) if r else P.g
        s = fit(c, t, d)
        if s is None:
            return None
        r.append((c, s))
    return r


def k_routes(P, out, k):
    first = dijkstra(P, out, P.src, P.g, set(), set())
    if not first:
        return
    done = [first]
    yield first[1]
    cand, seen, tick = [], {tuple(c.id for c, _ in first[1])}, 0
    while len(done) < k:
        last = done[-1][1]
        for i in range(len(last)):
            root = [c for c, _ in last[:i]]
            rid = tuple(c.id for c in root)
            ban = {r[i][0].id for _, r in done
                   if len(r) > i and tuple(c.id for c, _ in r[:i]) == rid}
            pre = reschedule(P, root)
            if root and pre is None:
                continue
            n = root[-1].v if root else P.src
            t = pre[-1][1] + P.S / root[-1].r + root[-1].d if root else P.g
            ban_n = {P.src} | {c.v for c in root[:-1]} if root else set()
            sp = dijkstra(P, out, n, t, ban, ban_n, pre[-1] if root else None)
            if not sp:
                continue
            full = (pre or []) + sp[1]
            ids = tuple(c.id for c, _ in full)
            if ids in seen:
                continue
            seen.add(ids)
            tick += 1
            heapq.heappush(cand, (sp[0], tick, full))
        if not cand:
            return
        a, _, f = heapq.heappop(cand)
        done.append((a, f))
        yield f


def plan(P, k):
    """回傳 (schedule, 試過的路徑數)。"""
    out, tried = out_index(P.cs), 0
    for r in k_routes(P, out, k):
        tried += 1
        if validate(P, r):
            return r, tried
    return None, tried
