#!/usr/bin/env python3
"""檢查你的 my_dtn.py。在 src/practice 底下執行：

    python3 check.py 1        只檢查關卡 1
    python3 check.py 1-4      檢查關卡 1 到 4
    python3 check.py all      全部

每一關先跑教材例子的固定題，再拿隨機小案例和原本的程式（src/algorithm）逐一比對。
"""
import os
import random
import sys
import traceback
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
sys.path[:0] = [HERE, SRC, os.path.join(SRC, "experiments", "dtn_validation")]

import my_dtn as my                                   # noqa: E402  你的版本
from algorithm import model as rm, ours as ro, validate as rv   # noqa: E402  原版
from dtn import oracle, topology                      # noqa: E402  測資產生器與窮舉


class Fail(Exception):
    pass


def eq(got, want, what):
    if got != want:
        raise Fail("%s\n    你的答案：%r\n    正確答案：%r" % (what, got, want))


def fr(v):
    return [Fr(x) for x in v]


# ---------------------------------------------------------------------------
# 共用：教材例子、轉換、取樣點
# ---------------------------------------------------------------------------

def book(ct=False, mod=my):
    """第 4、9 章例子，用 mod（my 或原版 model）的型別建立。"""
    Contact, Problem, Curve = mod.Contact, mod.Problem, mod.Curve
    c1 = Contact("c1", "A", "B", Fr(100), Fr(150), Fr(1), Fr(0), ())
    c2 = Contact("c2", "B", "C", Fr(110), Fr(160), Fr(1), Fr(0), ())
    O = Curve(fr([100, 110, 120, 130]), fr([0, 10, 10, 0]), fr([0, 10, 10, 0]))
    return Problem([c1, c2], "A", "C", Fr(100), Fr(10), Fr(15), {"B": O}, Fr(1000), ct), c1, c2


def to_my(P):
    """原版 Problem → 你的 Problem（Curve 換成你的 Curve）。"""
    O = {n: my.Curve(cv.ts, cv.ls, cv.rs) for n, cv in P.O.items()}
    cs = [my.Contact(*c) for c in P.cs]
    return my.Problem(cs, P.src, P.dst, P.g, P.S, P.M, O, P.T, P.ct)


def samples(ts):
    """曲線比對用的時刻：每個變化點、前後一點點、兩點中間、範圍外。"""
    if not ts:
        return [Fr(0), Fr(5)]
    pts = set(ts)
    for t in ts:
        pts |= {t - Fr(1, 3), t + Fr(1, 3)}
    for a, b in zip(ts, ts[1:]):
        pts.add((a + b) / 2)
    pts |= {ts[0] - 1, ts[-1] + 1}
    return sorted(pts)


def cases(n, ct=False):
    """隨機小案例：每個案例依序規劃多包，回傳每一包規劃前的原版 Problem。"""
    for seed in range(1, n + 1):
        P, bundles = topology.small_case(seed)
        P = rm.Problem(*P)._replace(ct=ct)
        for u, v, g in bundles:
            P = P._replace(src=u, dst=v, g=g)
            yield seed, P
            sch = ro.plan(P)
            if sch:
                P = rv.commit(P, sch)


def grid_times(P, c, step=Fr(1, 4)):
    x, out = Fr(int(c.a / step)) * step, []
    while x <= c.b:
        out.append(x)
        x += step
    return out


# ---------------------------------------------------------------------------
# 關卡
# ---------------------------------------------------------------------------

def level1():
    eq(my.ramp(Fr(120), Fr(115), Fr(125), Fr(10)), Fr(5), "ramp(120, 115, 125, 10)")
    eq(my.ramp(Fr(110), Fr(115), Fr(125), Fr(10)), Fr(0), "ramp(110, 115, 125, 10)")
    eq(my.ramp(Fr(130), Fr(115), Fr(125), Fr(10)), Fr(10), "ramp(130, 115, 125, 10)")
    c1 = my.Contact("c1", 0, 1, Fr(0), Fr(100), Fr(2), Fr(0), ())
    c2 = my.Contact("c2", 1, 2, Fr(0), Fr(100), Fr(4), Fr(0), ())
    P = my.Problem([c1, c2], 0, 2, Fr(0), Fr(20), Fr(30), {}, Fr(1000))
    eq(my.lag(P, c1, c2), Fr(10), "lag 收完才轉（S=20, r1=2, r2=4）")
    eq(my.lag(P._replace(ct=True), c1, c2), Fr(5), "lag 邊收邊轉（S=20, r1=2, r2=4）")
    eq(my.lag(P._replace(ct=True), c2, c1), Fr(0), "lag 邊收邊轉（r1=4, r2=2，不能是負的）")
    rnd = random.Random(1)
    for _ in range(300):
        a = Fr(rnd.randint(0, 20)); b = a + Fr(rnd.randint(1, 20), 2)
        t = Fr(rnd.randint(-10, 50), 2); S = Fr(rnd.randint(1, 9))
        eq(my.ramp(t, a, b, S), rm.ramp(t, a, b, S), "ramp(%s, %s, %s, %s)" % (t, a, b, S))


def level2():
    P, _, _ = book()
    O = P.O["B"]
    eq(O.left(Fr(125)), Fr(5), "left(125)")
    eq(O.left(Fr(105)), Fr(5), "left(105)")
    eq(O.right(Fr(110)), Fr(10), "right(110)")
    eq(O.left(Fr(90)), Fr(0), "left(90)，第一點之前")
    eq(O.right(Fr(140)), Fr(0), "right(140)，最後一點之後")
    eq(my.Curve().left(Fr(100)), Fr(0), "空曲線 left(100)")
    eq(O.between(Fr(100), Fr(130)), fr([110, 120]), "between(100, 130)")
    eq(O.between(Fr(130), Fr(100)), [], "between(130, 100)")
    eq(O.peak(Fr(100), Fr(130)), Fr(10), "peak(100, 130)")
    eq(O.peak(Fr(112), Fr(118)), Fr(10), "peak(112, 118)")
    eq(O.peak(Fr(125), Fr(140)), Fr(5), "peak(125, 140)")
    # 有跳變的曲線：目的地在 110 交付歸零
    J = my.Curve(fr([100, 110]), fr([0, 10]), fr([0, 0]))
    eq(J.left(Fr(110)), Fr(10), "跳變曲線 left(110)")
    eq(J.right(Fr(110)), Fr(0), "跳變曲線 right(110)")
    eq(J.top(Fr(110)), Fr(10), "跳變曲線 top(110)")
    n = 0
    for seed, P in cases(150):
        for node, ref in P.O.items():
            mine = my.Curve(ref.ts, ref.ls, ref.rs)
            ss = samples(ref.ts)
            for t in ss:
                for name in ("left", "right", "top"):
                    eq(getattr(mine, name)(t), getattr(ref, name)(t),
                       "隨機案例 %d 節點 %s 的 %s(%s)" % (seed, node, name, t))
            for a, b in zip(ss, ss[2:]):
                eq(mine.between(a, b), ref.between(a, b), "隨機案例 %d between(%s, %s)" % (seed, a, b))
                eq(mine.peak(a, b), ref.peak(a, b), "隨機案例 %d peak(%s, %s)" % (seed, a, b))
            n += 1
    return "比對 %d 條隨機曲線" % n


def level3():
    a = my.Curve(fr([100, 110, 120, 130]), fr([0, 10, 10, 0]), fr([0, 10, 10, 0]))
    b = my.Curve(fr([115, 125, 135]), fr([0, 10, 0]), fr([0, 10, 0]))
    s = a.add(b)
    for t, want in ((115, 10), (120, 15), (125, 15), (130, 5), (135, 0)):
        eq(s.left(Fr(t)), Fr(want), "舊包 + 新包 在 %d 的值" % t)
    n = 0
    for seed, P in cases(150):
        curves = list(P.O.values())
        for x, y in zip(curves, curves[1:]):
            want = x.add(y)
            got = my.Curve(x.ts, x.ls, x.rs).add(my.Curve(y.ts, y.ls, y.rs))
            for t in samples(want.ts):
                eq((got.left(t), got.right(t)), (want.left(t), want.right(t)),
                   "隨機案例 %d 相加後在 %s 的 (左, 右)" % (seed, t))
            n += 1
    return "比對 %d 組相加" % n


def level4():
    P, c1, c2 = book()
    eq(my.relay_ok(P, c1, Fr(115), c2, Fr(125)), True, "第 4 章：relay_ok(s1=115, s2=125)")
    eq(my.relay_ok(P, c1, Fr(114), c2, Fr(124)), False, "第 4 章：relay_ok(s1=114, s2=124)（120 秒合計 16）")
    eq(my.relay_ok(P, c1, Fr(115), c2, Fr(124)), False, "第 4 章：relay_ok(s1=115, s2=124)（還沒收完）")
    Pc = P._replace(ct=True)
    eq(my.relay_ok(Pc, c1, Fr(110), c2, Fr(110)), True, "邊收邊轉：relay_ok(110, 110)")
    eq(my.validate(P, [(c1, Fr(115)), (c2, Fr(125))]), True, "validate 收完才轉的答案")
    n = 0
    for ct in (False, True):
        for seed, P in cases(60, ct):
            M = to_my(P)
            for c in P.cs:
                for s in grid_times(P, c):
                    cm = my.Contact(*c)
                    eq(my.hop_ok(M, cm, s), rv.hop_ok(P, c, s), "隨機案例 %d hop_ok(%s, %s)" % (seed, c.id, s))
                    if c.u == P.src:
                        eq(my.source_ok(M, cm, s), rv.source_ok(P, c, s), "隨機案例 %d source_ok(%s, %s)" % (seed, c.id, s))
                    if c.v == P.dst:
                        eq(my.destination_ok(M, cm, s), rv.destination_ok(P, c, s),
                           "隨機案例 %d destination_ok(%s, %s)" % (seed, c.id, s))
                    for d in P.cs:
                        if d.u != c.v:
                            continue
                        for s2 in grid_times(P, d, Fr(1, 2)):
                            eq(my.relay_ok(M, cm, s, my.Contact(*d), s2), rv.relay_ok(P, c, s, d, s2),
                               "隨機案例 %d（ct=%s）relay_ok(%s@%s, %s@%s)" % (seed, ct, c.id, s, d.id, s2))
                            n += 1
            sch = ro.plan(P)
            if sch:
                eq(my.validate(M, [(my.Contact(*c), s) for c, s in sch]), True, "隨機案例 %d：原版排程應該合法" % seed)
    return "比對 %d 次 relay_ok 與其他規則" % n


def level5():
    eq(my.subtract_open([(Fr(105), Fr(150))], Fr(110), Fr(130)), [(Fr(105), Fr(110)), (Fr(130), Fr(150))],
       "[(105,150)] 扣掉 (110,130)")
    eq(my.merge([(Fr(110), Fr(120)), (Fr(100), Fr(110))]), [(Fr(100), Fr(120))], "merge 相接")
    c = my.Contact("c", 0, 1, Fr(100), Fr(160), Fr(2), Fr(0), ((Fr(120), Fr(130)),))
    P = my.Problem([c], 0, 1, Fr(100), Fr(20), Fr(30), {}, Fr(1000))
    eq(my.candidate_range(P, c, Fr(105)), [(Fr(105), Fr(110)), (Fr(130), Fr(150))], "candidate_range 例子")
    rnd = random.Random(5)
    for _ in range(500):
        parts = ro.merge([(Fr(a), Fr(a + rnd.randint(0, 6))) for a in rnd.sample(range(30), 4)])
        x = Fr(rnd.randint(0, 40), 2); y = x + Fr(rnd.randint(1, 12), 2)
        eq(my.subtract_open(parts, x, y), ro.subtract_open(parts, x, y), "subtract_open(%s, %s, %s)" % (parts, x, y))
        raw = [(Fr(a), Fr(a + rnd.randint(0, 6))) for a in (rnd.randint(0, 30) for _ in range(5))]
        eq(my.merge(raw), ro.merge(raw), "merge(%s)" % raw)
    n = 0
    for seed, P in cases(200):
        M = to_my(P)
        for c in P.cs:
            for head in (Fr(0), Fr(3), Fr(13, 2)):
                eq(my.candidate_range(M, my.Contact(*c), head), ro.candidate_range(P, c, head),
                   "隨機案例 %d candidate_range(%s, head=%s)" % (seed, c.id, head))
                n += 1
    return "比對 %d 次 candidate_range" % n


def level6():
    P, c1, c2 = book()
    Q = my.commit(P, [(c1, Fr(115)), (c2, Fr(125))])
    for t, want in ((110, 10), (115, 10), (120, 15), (125, 15), (130, 5), (135, 0)):
        eq(Q.O["B"].left(Fr(t)), Fr(want), "第 4 章 commit 後 B 在 %d 的值" % t)
    eq(dict((c.id, c.F) for c in Q.cs)["c2"], ((Fr(125), Fr(135)),), "commit 後 c2 的預約 F")
    eq("B" in P.O and P.O["B"].left(Fr(120)), Fr(10), "commit 不能改到原本的 P.O")
    n = 0
    for ct in (False, True):
        for seed, P in cases(200, ct):
            sch = ro.plan(P)
            if not sch:
                continue
            want = rv.commit(P, sch)
            got = my.commit(to_my(P), [(my.Contact(*c), s) for c, s in sch])
            eq([c.F for c in got.cs], [c.F for c in want.cs], "隨機案例 %d commit 後的 F" % seed)
            for node, cv in want.O.items():
                for t in samples(cv.ts):
                    eq((got.O[node].left(t), got.O[node].right(t)), (cv.left(t), cv.right(t)),
                       "隨機案例 %d（ct=%s）commit 後節點 %s 在 %s 的 (左, 右)" % (seed, ct, node, t))
            n += 1
    return "比對 %d 次 commit" % n


def level7():
    P, c1, c2 = book()
    sch = my.plan_simple(P)
    eq(sch and [(c.id, s) for c, s in sch], [("c1", Fr(115)), ("c2", Fr(125))], "第 4 章收完才轉的排程")
    n = 0
    for seed, P in cases(80):
        want = oracle.earliest(P, Fr(1, 16))
        M = to_my(P)
        sch = my.plan_simple(M)
        got = my.arrival(M, sch) if sch else None
        if sch:
            eq(rv.validate(P, [(rm.Contact(*c), s) for c, s in sch]), True, "隨機案例 %d：你的排程不合法" % seed)
        eq(got, want, "隨機案例 %d 的最早到達（和窮舉比）" % seed)
        n += 1
    return "和窮舉比對 %d 包" % n


def level8():
    for ct, want in ((False, [("c1", Fr(115)), ("c2", Fr(125))]), (True, [("c1", Fr(110)), ("c2", Fr(110))])):
        P, _, _ = book(ct)
        sch = my.plan(P)
        eq(sch and [(c.id, s) for c, s in sch], want, "第 4／9 章例子（ct=%s）" % ct)
    n = 0
    for ct in (False, True):
        for seed, P in cases(300, ct):
            ref = ro.plan(P)
            M = to_my(P)
            sch = my.plan(M)
            if sch:
                eq(rv.validate(P, [(rm.Contact(*c), s) for c, s in sch]), True,
                   "隨機案例 %d（ct=%s）：你的排程不合法" % (seed, ct))
            eq(my.arrival(M, sch) if sch else None, rm.arrival(P, ref) if ref else None,
               "隨機案例 %d（ct=%s）的到達時間（和原版比）" % (seed, ct))
            n += 1
    return "和原版比對 %d 包" % n


LEVELS = {1: level1, 2: level2, 3: level3, 4: level4, 5: level5, 6: level6, 7: level7, 8: level8}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        todo = sorted(LEVELS)
    elif "-" in arg:
        a, b = map(int, arg.split("-"))
        todo = list(range(a, b + 1))
    else:
        todo = [int(arg)]
    for k in todo:
        try:
            note = LEVELS[k]()
            print("關卡 %d：通過%s" % (k, "（%s）" % note if note else ""))
        except NotImplementedError:
            print("關卡 %d：還沒寫" % k)
            return
        except Fail as e:
            print("關卡 %d：錯誤\n  %s" % (k, e))
            return
        except Exception:
            print("關卡 %d：程式出錯" % k)
            traceback.print_exc()
            return


if __name__ == "__main__":
    main()
