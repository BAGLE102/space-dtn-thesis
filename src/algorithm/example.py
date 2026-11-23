#!/usr/bin/env python3
"""教材第 4、9 章的例子：同一包用收完才轉和邊收邊轉各排一次。

執行（在 src/ 底下）：python3 -m algorithm.example

設定（教學用假設）：
    路徑 A → B → C，c1（A→B）開 100～150，c2（B→C）開 110～160，速率都是 1 MB/s
    B 的 Buffer 上限 15 MB；B 上已有一個舊包 10 MB：
        100～110 收、110～120 停留、120～130 送出
    新包 10 MB，100 秒在 A 產生
"""
from fractions import Fraction as Fr

from .model import Contact, Curve, Problem, arrival
from .ours import plan
from .validate import commit, validate

A, B, C = "A", "B", "C"
c1 = Contact("c1", A, B, Fr(100), Fr(150), Fr(1), Fr(0), ())
c2 = Contact("c2", B, C, Fr(110), Fr(160), Fr(1), Fr(0), ())

# 舊包在 B 的占用：ts / ls / rs（A、C 沒有其他包）
old_B = Curve([Fr(100), Fr(110), Fr(120), Fr(130)],
              [Fr(0), Fr(10), Fr(10), Fr(0)],
              [Fr(0), Fr(10), Fr(10), Fr(0)])

for ct, name in ((False, "收完才轉"), (True, "邊收邊轉")):
    # Problem(cs, src, dst, g, S, M, O, T, ct)
    P = Problem([c1, c2], A, C, Fr(100), Fr(10), Fr(15), {B: old_B}, Fr(1000), ct)
    sch = plan(P)
    print(name)
    for c, s in sch:
        print("  %s 在 %s 出發" % (c.id, s))
    print("  %s 到 C，回放檢查：%s" % (arrival(P, sch), validate(P, sch)))
    P2 = commit(P, sch)
    O = P2.O[B]
    print("  排定後 B 的 O_n：ts =", [int(t) for t in O.ts])
    print("                   值 =", [int(v) for v in O.ls])
