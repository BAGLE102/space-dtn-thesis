"""模型：Contact、Problem、分段線性占用曲線。全部用 Fraction 精確計算。

占用曲線允許跳變。每個頂點存左極限 l 與右極限 r。
"""
from bisect import bisect_left, bisect_right
from collections import namedtuple
from fractions import Fraction as Fr

Contact = namedtuple("Contact", "id u v a b r d F")
# cs: contacts; src,dst,g,S: 目前 bundle; M: 所有節點 buffer 上限
# O: {node: Curve}; T: 期限 D*; F 存在 Contact 內
# ct: True 為 cut-through（邊收邊送）；False（預設）為 store-and-forward（收完才送）
Problem = namedtuple("Problem", "cs src dst g S M O T ct", defaults=(False,))


def lag(P, c1, c2):
    """前一跳起送 s1 到下一跳最早起送 s2 的最小間隔（不含傳播延遲）。

    store-and-forward：s2 ≥ A = s1 + d + S/r1，間隔 S/r1。
    cut-through：s2 ≥ max(h, A − S/r2)，間隔 max(0, S/r1 − S/r2)。
    """
    d1, d2 = P.S / c1.r, P.S / c2.r
    return max(Fr(0), d1 - d2) if P.ct else d1


class Curve:
    __slots__ = ("ts", "ls", "rs")

    def __init__(self, ts=(), ls=(), rs=()):
        self.ts, self.ls, self.rs = list(ts), list(ls), list(rs)

    def _between(self, i, t):
        x0, y0, x1, y1 = self.ts[i - 1], self.rs[i - 1], self.ts[i], self.ls[i]
        return y0 + (y1 - y0) * (t - x0) / (x1 - x0)

    def left(self, t):
        if not self.ts:
            return Fr(0)
        i = bisect_left(self.ts, t)
        if i == len(self.ts):
            return self.rs[-1]
        if self.ts[i] == t or i == 0:
            return self.ls[i]
        return self._between(i, t)

    def right(self, t):
        if not self.ts:
            return Fr(0)
        i = bisect_left(self.ts, t)
        if i == len(self.ts):
            return self.rs[-1]
        if self.ts[i] == t:
            return self.rs[i]
        if i == 0:
            return self.ls[0]
        return self._between(i, t)

    def top(self, t):
        return max(self.left(t), self.right(t))

    def between(self, a, b):
        """嚴格落在 (a, b) 內的頂點時間。"""
        return self.ts[bisect_right(self.ts, a):bisect_left(self.ts, b)] if a < b else []

    def peak(self, a, b):
        """[a, b] 內的最高占用。"""
        vals = [self.top(a), self.top(b)]
        vals += [self.top(x) for x in self.between(a, b)]
        return max(vals)

    def global_peak(self):
        if not self.ts:
            return Fr(0), None
        best, when = None, None
        for t, l, r in zip(self.ts, self.ls, self.rs):
            if best is None or max(l, r) > best:
                best, when = max(l, r), t
        return best, when

    def add(self, o):
        ts = sorted(set(self.ts) | set(o.ts))
        ls = [self.left(t) + o.left(t) for t in ts]
        rs = [self.right(t) + o.right(t) for t in ts]
        return Curve(*_prune(ts, ls, rs))


def _prune(ts, ls, rs):
    """移除共線且沒有跳變的頂點，避免曲線越累積越慢。"""
    if len(ts) < 3:
        return ts, ls, rs
    T, L, R = [ts[0]], [ls[0]], [rs[0]]
    for i in range(1, len(ts) - 1):
        if ls[i] == rs[i]:
            x0, y0, x1, y1 = T[-1], R[-1], ts[i + 1], ls[i + 1]
            if (ls[i] - y0) * (x1 - x0) == (y1 - y0) * (ts[i] - x0):
                continue
        T.append(ts[i])
        L.append(ls[i])
        R.append(rs[i])
    T.append(ts[-1])
    L.append(ls[-1])
    R.append(rs[-1])
    return T, L, R


def ramp(t, a, b, S):
    """從 a 到 b 線性由 0 增加到 S。"""
    if t <= a:
        return Fr(0)
    if t >= b:
        return S
    return S * (t - a) / (b - a)


def arrival(P, sch):
    c, s = sch[-1]
    return s + P.S / c.r + c.d


def out_index(cs):
    out = {}
    for c in cs:
        out.setdefault(c.u, []).append(c)
    return out
