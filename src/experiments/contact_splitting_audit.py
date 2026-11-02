"""Contact splitting 單包查核（2026-11-02）。

候選搜尋與暴力 oracle 都用 Fraction。oracle 不使用 J、H 或 dominance：逐一列舉
1/16 秒格點上的起送時間，直接檢查等待／送出／接收條件。
範圍：一般中繼節點的連續背景；來源與目的地無背景，所以不測 P 跳變端點。
這不是一般證明，也不是完整多包路由器。
"""
import argparse, heapq, json, random
from collections import Counter, namedtuple
from fractions import Fraction as Fr

Contact = namedtuple("Contact", "id u v a b r delay R F")
Inst = namedtuple("Inst", "contacts src dst g S M O horizon")
GRID = Fr(1, 16)
INF = 10**9


def occ(curve, t):
    """分段線性 O(t)；curve=[(t,v),...]，範圍外取端點值。"""
    if not curve: return Fr(0)
    if t <= curve[0][0]: return curve[0][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if t <= x1: return y0 + (y1 - y0) * (t - x0) / (x1 - x0)
    return curve[-1][1]


def trap(t0, size, hold, rate=Fr(4)):
    rise = size / rate
    return [(t0, Fr(0)), (t0 + rise, size), (t0 + rise + hold, size), (t0 + 2 * rise + hold, Fr(0))]


def add_curves(curves):
    ts = sorted({t for c in curves for t, _ in c})
    return [(t, sum(occ(c, t) for c in curves)) for t in ts]


def hold_ok(I, n, t0, t1):
    pts = {t0, t1} | {t for t, _ in I.O.get(n, []) if t0 < t < t1}
    return all(occ(I.O.get(n, []), t) + I.S <= I.M for t in pts)


def hop_ok(I, c, s):
    """oracle 用：直接檢查單跳送出與接收。"""
    d = I.S / c.r; f = s + d; h = s + c.delay; A = f + c.delay
    if s < c.a or f > c.b or A > I.horizon: return False
    if any(s < y and x < f for x, y in c.F): return False
    Ou, Ov = I.O.get(c.u, []), I.O.get(c.v, [])
    for t in {s, f} | {x for x, _ in Ou if s < x < f}:
        if occ(Ou, t) + I.S - c.r * (t - s) > I.M: return False
    for t in {h, A} | {x for x, _ in Ov if h < x < A}:
        if occ(Ov, t) + c.r * (t - h) > I.M: return False
    return True


def oracle(I):
    """窮舉 walk：回傳最早抵達與其排程；狀態含每個 contact 使用次數。"""
    out = {}
    for c in I.contacts: out.setdefault(c.u, []).append(c)
    pq = [(I.g, 0, I.src, (), ())]; seen = set(); tick = 0
    while pq:
        A, _, n, cnt, sch = heapq.heappop(pq)
        if n == I.dst: return A, sch
        key = (n, A, cnt)
        if key in seen: continue
        seen.add(key)
        for c in out.get(n, []):
            used = dict(cnt).get(c.id, 0)
            if I.S * (used + 1) > c.R: continue
            s = max(A, c.a)
            s = Fr((s / GRID).__ceil__()) * GRID
            while s + I.S / c.r <= c.b:
                if not hold_ok(I, n, A, s): break
                if hop_ok(I, c, s):
                    new = dict(cnt); new[c.id] = used + 1; tick += 1
                    B = s + I.S / c.r + c.delay
                    heapq.heappush(pq, (B, tick, c.v, tuple(sorted(new.items())), sch + ((c.id, s),)))
                s += GRID
    return None, ()


def crossings(curve, level):
    res = []
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if y0 != y1 and min(y0, y1) <= level <= max(y0, y1):
            res.append(x0 + (level - y0) * (x1 - x0) / (y1 - y0))
    return res


def solve_set(lo, hi, crit, ok):
    """由臨界點與中點重建閉區間聯集；非閉集合會觸發 assert。"""
    if lo > hi: return []
    pts = sorted({p for p in crit if lo < p < hi} | {lo, hi})
    parts = []; cur = None
    for i, p in enumerate(pts):
        if ok(p):
            if cur is None: cur = [p, p]
            else: cur[1] = p
        else:
            if i and ok((pts[i - 1] + p) / 2): raise AssertionError('open right endpoint')
            if cur: parts.append(tuple(cur)); cur = None
        if i + 1 < len(pts):
            m = (p + pts[i + 1]) / 2
            if not ok(m):
                if cur: parts.append(tuple(cur)); cur = None
            elif cur is None:
                raise AssertionError("open left endpoint")
    if cur: parts.append(tuple(cur))
    return parts


def start_set(I, c):
    """公式式求 J：不逐格點；只含 contact 時窗、F、送出、接收條件。"""
    d = I.S / c.r
    hi = min(c.b - d, I.horizon - d - c.delay)
    Ou, Ov = I.O.get(c.u, []), I.O.get(c.v, [])
    cr = set()
    for x, y in c.F: cr |= {x - d, y}
    for x, y in Ou:
        cr |= {x, x - d, x + (I.M - y - I.S) / c.r}
    for x, y in Ov:
        cr |= {x - c.delay, x - d - c.delay, x - c.delay - (I.M - y) / c.r}
    for z in crossings(Ou, I.M - I.S): cr |= {z, z - d}
    for z in crossings(Ou, I.M): cr |= {z, z - d}
    for z in crossings(Ov, I.M): cr.add(z - c.delay)
    for z in crossings(Ov, I.M - I.S): cr.add(z - d - c.delay)
    def ok(s):
        if any(s < y and x < s + d for x, y in c.F): return False
        f = s + d; h = s + c.delay; A = f + c.delay
        for x in [s, f] + [t for t, _ in Ou if s < t < f]:
            if occ(Ou, x) + I.S - c.r * (x - s) > I.M: return False
        for x in [h, A] + [t for t, _ in Ov if h < t < A]:
            if occ(Ov, x) + c.r * (x - h) > I.M: return False
        return True
    # F 的洞是開區間，兩側端點可行，solve_set 會逐片保留。
    return solve_set(c.a, hi, cr, ok)


def hold_set(I, n):
    curve = I.O.get(n, [])
    cr = {t for t, _ in curve} | set(crossings(curve, I.M - I.S))
    return solve_set(Fr(-1000), Fr(1000), cr, lambda t: occ(curve, t) + I.S <= I.M)


def comp_end(H, t):
    for a, b in H:
        if a <= t <= b: return (a, b)
    return None


def search(I, mode="candidate"):
    """mode 控制對照版本；candidate 依使用者澄清，於 Label 延伸時才判定；precut 為搜尋前全圖計算。"""
    H = {n: hold_set(I, n) for c in I.contacts for n in (c.u, c.v)}
    H.setdefault(I.src, [(Fr(-1000), Fr(1000))])
    J = {}; stat = dict(gaps=0)
    def parts_of(c):
        """Label 延伸到 c 時才判定 J；快照固定，同一 contact 只算一次。"""
        if c.id in J: return J[c.id]
        d = I.S / c.r
        parts = start_set(I, c)
        stat["gaps"] += sum(1 for x, y in zip(parts, parts[1:]) if y[0] - x[1] < d)
        if mode == "double_subtract":
            parts = [(a, b - d) for a, b in parts if b - d >= a]
        elif mode == "delete_receiver_gap":
            # 錯誤映射：把接收端不可完整持有時段直接從傳送端時窗刪掉。
            parts = []
            for a, b in H.get(c.v, []):
                lo, hi = max(a, c.a), min(b, c.b)
                if hi - lo >= d: parts.append((lo, hi - d))
        elif mode == "merge_small_gap":
            m = []
            for p in parts:
                if m and p[0] - m[-1][1] < d: m[-1] = (m[-1][0], p[1])
                else: m.append(p)
            parts = m
        J[c.id] = parts
        return parts
    if mode == "precut":
        for c in I.contacts: parts_of(c)
    out = {}
    for c in I.contacts: out.setdefault(c.u, []).append(c)
    L0 = dict(c=None, A=I.g, s=None, pred=None, n=I.src, cnt={}, live=True)
    pq = [(I.g, 0, L0)]; tick = 0; kept = {}; created = 0
    def dominated(a, b):
        if mode == "early_only": return a["A"] <= b["A"]
        if a["n"] == I.dst: return a["A"] <= b["A"]
        if comp_end(H[a["n"]], a["A"]) != comp_end(H[a["n"]], b["A"]) or a["A"] > b["A"]: return False
        if mode in ("no_count", "pure_F"): return True
        return all(a["cnt"].get(k, 0) <= v for k, v in b["cnt"].items()) and all(k in b["cnt"] for k in a["cnt"] if a["cnt"][k])
    while pq:
        A, _, L = heapq.heappop(pq)
        if not L["live"]: continue
        if L["n"] == I.dst:
            sch = []; x = L
            while x["pred"]: sch.append((x["c"], x["s"])); x = x["pred"]
            return A, tuple(reversed(sch)), dict(created=created, small_gap=stat["gaps"], evaluated=len(J), contacts=len(I.contacts))
        hend = comp_end(H[L["n"]], A)
        if hend is None: raise AssertionError("label outside H")
        for c in out.get(L["n"], []):
            used = L["cnt"].get(c.id, 0)
            if I.S * (used + 1) > c.R: continue
            parts = parts_of(c)
            picks = []
            for a, b in parts:
                lo, hi = max(a, A), min(b, hend[1])
                if lo <= hi: picks.append(lo)
            if mode == "first_part_only": picks = picks[:1]
            for s in picks:
                B = s + I.S / c.r + c.delay
                N = dict(c=c.id, A=B, s=s, pred=L, n=c.v, cnt={**L["cnt"], c.id: used + 1}, live=True)
                created += 1
                if c.v != I.dst and comp_end(H[c.v], B) is None:
                    if mode == "candidate": raise AssertionError("receive-feasible label not holdable")
                    continue
                pool = kept.setdefault(c.v, [])
                if any(dominated(o, N) for o in pool): continue
                for o in pool:
                    if dominated(N, o): o["live"] = False
                pool.append(N); tick += 1
                heapq.heappush(pq, (B, tick, N))
    return None, (), dict(created=created, small_gap=stat["gaps"], evaluated=len(J), contacts=len(I.contacts))


def validate(I, sch):
    """獨立重放排程：等待、單跳與 quota。"""
    by = {c.id: c for c in I.contacts}; A = I.g; n = I.src; used = Counter()
    for cid, s in sch:
        c = by[cid]; used[cid] += 1
        if c.u != n or s < A or not hold_ok(I, n, A, s) or not hop_ok(I, c, s) or used[cid] * I.S > c.R: return False
        A = s + I.S / c.r + c.delay; n = c.v
    return n == I.dst


def C(id, u, v, a, b, delay=0, R=INF, F=()):
    return Contact(id, u, v, Fr(a), Fr(b), Fr(4), Fr(delay), R, tuple((Fr(x), Fr(y)) for x, y in F))


BASE_O = [(Fr(2), Fr(0)), (Fr(3), Fr(4)), (Fr(6), Fr(4)), (Fr(7), Fr(0))]
def ppt_second(c7_R=2, c4=(7, 9), c5=(10, 11), c4_delay=0):
    cs = [C("c1", "X", "B", 2, 3, R=0, F=[(2, 3)]), C("c2", "B", "D", 6, 7, 1, R=0, F=[(6, 7)]),
          C("c3", "A", "B", 1, 2, R=4), C("c4", "A", "B", *c4, c4_delay, R=8), C("c5", "B", "D", *c5, 1, R=4),
          C("c6", "A", "C", 1, 2, 1, R=4), C("c7", "C", "D", 4, 5, R=c7_R), C("c8", "C", "D", 2, 3, R=4)]
    return Inst(cs, "A", "D", Fr(1), Fr(4), Fr(4), {"B": BASE_O}, Fr(16))
def ppt_first():
    cs = [C("c1", "X", "B", 2, 3, R=4), C("c2", "B", "D", 6, 7, 1, R=4), C("c3", "A", "B", 1, 2, R=4),
          C("c4", "A", "B", 7, 9, R=8), C("c5", "B", "D", 10, 11, 1, R=4), C("c6", "A", "C", 1, 2, 1, R=4),
          C("c7", "C", "D", 4, 5, R=2), C("c8", "C", "D", 2, 3, R=4)]
    return Inst(cs, "X", "D", Fr(0), Fr(4), Fr(4), {}, Fr(16))


def show(x): return None if x is None else str(x)
def run_case(name, I, modes=()):
    o, os = oracle(I); a, s, st = search(I)
    row = dict(case=name, oracle=show(o), candidate=show(a), schedule=[(k, str(v)) for k, v in s], labels=st["created"],
               valid=(validate(I, s) if s else None), J={c.id: [[str(x), str(y)] for x, y in start_set(I, c)] for c in I.contacts})
    for m in modes: row[m] = show(search(I, m)[0])
    return row


def rand_inst(rng, quota):
    nodes = ["S", "U", "V", "W", "T"]; cs = []
    for i in range(rng.randint(5, 9)):
        u = rng.choice(nodes[:4]); v = rng.choice([n for n in nodes[1:] if n != u])
        a = Fr(rng.randint(0, 20), 2); ln = Fr(rng.randint(2, 8), 2)
        fs = []
        if rng.random() < .25:
            x = a + Fr(rng.randint(0, 4), 2); fs = [(x, x + Fr(rng.randint(1, 3), 4))]
        R = rng.choice([1, 2, 4, 8]) if quota and rng.random() < .6 else INF
        cs.append(Contact(f"c{i}", u, v, a, a + ln, Fr(4), Fr(rng.choice([0, 0, 1, 2, 4]), 4), R, tuple(fs)))
    S = Fr(rng.choice([1, 2, 4])); M = Fr(rng.choice([4, 6]))
    O = {}
    for n in nodes[1:4]:
        cur = [trap(Fr(rng.randint(0, 24), 2), Fr(rng.choice([1, 2, 3, 4])), Fr(rng.randint(0, 6), 2)) for _ in range(rng.randint(0, 2))]
        if cur: O[n] = add_curves(cur)
    return Inst(cs, "S", "T", Fr(0), S, M, O, Fr(18))


def fuzz(n, seed, quota, modes):
    rng = random.Random(seed)
    res = dict(n=n, quota=quota, feasible=0, candidate_mismatch=0, invalid=0, small_gap_instances=0, label_max=0, eval_sum=0, contact_sum=0, modes={m: dict(mismatch=0, false_infeasible=0, later=0, invalid=0) for m in modes})
    fails = []
    for i in range(n):
        I = rand_inst(rng, quota); o, _ = oracle(I); a, s, st = search(I)
        res["feasible"] += o is not None; res["small_gap_instances"] += st["small_gap"] > 0; res["label_max"] = max(res["label_max"], st["created"]); res["eval_sum"] += st["evaluated"]; res["contact_sum"] += st["contacts"]
        if a != o: res["candidate_mismatch"] += 1; fails.append(dict(i=i, oracle=show(o), cand=show(a), inst=repr(I)))
        if s and not validate(I, s): res["invalid"] += 1
        for m in modes:
            x, sx, _ = search(I, m); r = res["modes"][m]
            if x != o:
                r["mismatch"] += 1
                if x is None: r["false_infeasible"] += 1
                elif o is None or x < o: r["invalid"] += 1
                else: r["later"] += 1
    res["fails"] = fails[:5]
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=1500); ap.add_argument("--seed", type=int, default=20261102); ap.add_argument("--out", default="audit_results.json")
    a = ap.parse_args()
    neg = ("precut", "early_only", "no_count", "double_subtract", "delete_receiver_gap", "first_part_only", "merge_small_gap")
    cases = [run_case("第一包（原PPT）", ppt_first(), neg), run_case("第二包（原PPT）", ppt_second(), neg),
             run_case("V1 第二包，c7無配額限制", ppt_second(c7_R=INF), neg),
             run_case("V2 c4=[6,9]，c5=[7,8]：同步收放", ppt_second(c4=(6, 9), c5=(7, 8), c7_R=2), neg),
             run_case("V3 c4=[5,9]且δ=1，c5=[7,8]：接收映射需平移", ppt_second(c4=(5, 9), c5=(7, 8), c4_delay=1), neg)]
    gap = Inst([C("in", "S", "U", 0, 6), C("out", "U", "T", 0, 12)], "S", "T", Fr(0), Fr(4), Fr(4), {"U": trap(Fr(2), Fr(1), Fr("1/4"))}, Fr(18))
    cases.append(run_case("V4 前包1MB造成小缺口", gap, neg))
    walk = Inst([C("a", "S", "U", 0, 1), C("b", "U", "V", 1, 2), C("c", "V", "U", 5, 6), C("e", "U", "T", 7, 8)], "S", "T", Fr(0), Fr(4), Fr(4), {"U": [(Fr(2), Fr(0)), (Fr(3), Fr(4)), (Fr(4), Fr(4)), (Fr(5), Fr(0))]}, Fr(18))
    cases.append(run_case("V5 必須離開再返回的walk", walk, neg))
    # V6：第 26 頁診斷例的可執行版本；早到但已用完 c，晚到仍可用 c。
    diag = Inst([C("x1", "X", "U", 0, "1/4"), C("c", "U", "V", 1, 6, R=1), C("x2", "V", "U", "19/4", 5), C("x3", "X", "U", "21/4", "11/2"), C("goal", "V", "T", 7, "29/4")],
                "X", "T", Fr(0), Fr(1), Fr(1), {"U": trap(Fr(2), Fr(1), Fr(5, 2)), "V": trap(Fr(19, 4), Fr(1), Fr(1, 4))}, Fr(18))
    cases.append(run_case("V6 第26頁容量歷史診斷例", diag, neg))
    # V7：小缺口不能合併；來源 5/4 才有資料，真正最早起送是 7/4，不是缺口內的 5/4。
    gap2 = Inst(gap.contacts, "S", "T", Fr(5, 4), Fr(4), Fr(4), gap.O, Fr(18))
    cases.append(run_case("V7 小缺口內不可起送", gap2, neg))
    out = dict(cases=cases, fuzz_no_quota=fuzz(a.n, a.seed, False, neg), fuzz_quota=fuzz(a.n, a.seed + 1, True, neg))
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    for k in ("fuzz_no_quota", "fuzz_quota"):
        print(k, json.dumps({x: y for x, y in out[k].items() if x != "fails"}, ensure_ascii=False)); print(out[k]["fails"][:1])
    for c in cases: print(json.dumps(c, ensure_ascii=False))
