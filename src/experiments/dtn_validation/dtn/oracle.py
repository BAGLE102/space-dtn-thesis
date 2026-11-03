"""單包窮舉：列出所有格點上的 (contact, 起送時間)。

不使用 Label 或區間，也不呼叫搜尋的篩選函式。收完才轉時，可否接續只看
相鄰兩跳，所以在 (contact, s) 圖上走訪即可涵蓋全部格點排程。
只能回答格點上的最早抵達；若最佳解落在格點之間，本方法可能更早。
"""
import math
from fractions import Fraction as Fr
from .model import out_index
from .validate import destination_ok, hop_ok, relay_ok, source_ok


def times(P, c, grid):
    d = P.S / c.r
    x = Fr(math.ceil(c.a / grid)) * grid
    res = []
    while x + d <= c.b and x + d + c.d <= P.T:
        if hop_ok(P, c, x):
            res.append(x)
        x += grid
    return res


def earliest(P, grid=Fr(1, 16)):
    out = out_index(P.cs)
    grid_times = {c.id: times(P, c, grid) for c in P.cs}
    best, stack, seen = None, [], set()

    def finish(c, s):
        nonlocal best
        if c.v == P.dst and destination_ok(P, c, s):
            A = s + P.S / c.r + c.d
            best = A if best is None else min(best, A)

    for c in out.get(P.src, []):
        for s in grid_times[c.id]:
            if s >= P.g and source_ok(P, c, s):
                seen.add((c.id, s))
                stack.append((c, s))
                finish(c, s)
    while stack:
        c, s = stack.pop()
        if c.v == P.dst:
            continue
        for c2 in out.get(c.v, []):
            for s2 in grid_times[c2.id]:
                if (c2.id, s2) not in seen and relay_ok(P, c, s, c2, s2):
                    seen.add((c2.id, s2))
                    stack.append((c2, s2))
                    finish(c2, s2)
    return best
