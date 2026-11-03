"""隨機拓樸與需求。相同參數與 seed 會得到相同結果。"""
import random
from fractions import Fraction as Fr
from .model import Contact, Curve, Problem


def random_contacts(seed, nodes, contacts, horizon, min_len, max_len, rates, delays):
    """隨機時變拓樸：每筆 contact 隨機抽節點對、開始時間、長度、速率、延遲。"""
    rng = random.Random("contacts-%s" % seed)
    res = []
    for i in range(contacts):
        u = rng.randrange(nodes)
        v = rng.randrange(nodes - 1)
        v = v + 1 if v >= u else v
        ln = rng.randint(min_len, max_len)
        a = rng.randint(0, max(0, horizon - ln))
        res.append(Contact("c%d" % i, u, v, Fr(a), Fr(a + ln),
                           Fr(rng.choice(rates)), Fr(str(rng.choice(delays))), ()))
    return res


def random_bundles(seed, n, nodes, release):
    rng = random.Random("bundles-%s" % seed)
    res = []
    for _ in range(n):
        u = rng.randrange(nodes)
        v = rng.randrange(nodes - 1)
        v = v + 1 if v >= u else v
        res.append((u, v, Fr(rng.randint(0, release))))
    res.sort(key=lambda x: x[2])
    return res


def _trap(rng):
    t = Fr(rng.randint(0, 24), 2)
    size = Fr(rng.choice([1, 2, 3, 4]))
    rise, hold = Fr(rng.choice([0, 1, 2]), 4), Fr(rng.randint(0, 6), 2)
    if rise == 0:
        return Curve([t, t + hold + Fr(1, 4)], [Fr(0), size], [size, Fr(0)])
    return Curve([t, t + rise, t + rise + hold + Fr(1, 4), t + 2 * rise + hold + Fr(1, 4)],
                 [Fr(0), size, size, Fr(0)], [Fr(0), size, size, Fr(0)])


def small_case(seed):
    """實驗 A 用的小案例：時間落在 1/4 秒格點，含背景占用與多包提交。"""
    rng = random.Random("small-%s" % seed)
    nodes = rng.randint(4, 6)
    cs = []
    for i in range(rng.randint(6, 14)):
        u = rng.randrange(nodes)
        v = rng.randrange(nodes - 1)
        v = v + 1 if v >= u else v
        a = Fr(rng.randint(0, 24), 2)
        cs.append(Contact("c%d" % i, u, v, a, a + Fr(rng.randint(2, 16), 2),
                          Fr(rng.choice([2, 4, 8])), Fr(rng.choice([0, 0, 1, 2, 4]), 4), ()))
    S = Fr(rng.choice([2, 4]))
    M = S + Fr(rng.choice([0, 0, 1, 2]))
    O = {}
    for n in range(nodes):
        if rng.random() < .6:
            cv = _trap(rng)
            for _ in range(rng.randint(0, 1)):
                cv = cv.add(_trap(rng))
            O[n] = cv
    bundles = []
    for _ in range(rng.randint(1, 3)):
        u = rng.randrange(nodes)
        v = rng.randrange(nodes - 1)
        v = v + 1 if v >= u else v
        bundles.append((u, v, Fr(rng.randint(0, 8))))
    bundles.sort(key=lambda x: x[2])
    return Problem(cs, None, None, Fr(0), S, M, O, Fr(30)), bundles
