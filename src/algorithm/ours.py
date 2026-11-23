"""本方法：區間 Label 搜尋。對應文件 Algorithm 2～6。

一包的處理流程：
    plan(P)
      search(P)                 找到最早到達目的地的 Label
        candidate_range         連線開放時間、期限、扣掉預約 → 可出發區間
        source_filter           來源的 Buffer
        buffer_filter           中繼的 Buffer
        destination_filter      目的地的 Buffer
          solve_region          細緻檢查（三個 filter 共用）
        insert                  去重後放進優先佇列
      backtrack(P, goal)        從終點回推每一跳的出發時間

P.ct = False：收完才轉（store-and-forward）
P.ct = True ：邊收邊轉（cut-through，送不能比收快）

本檔案與 src/experiments/dtn_validation/dtn/ours.py 的邏輯完全相同，只加了註解。
"""
import heapq
from collections import namedtuple
from fractions import Fraction as Fr
from .model import Curve, lag, out_index, ramp
from .validate import destination_ok, relay_ok, source_ok

# 搜尋中的一個狀態：
#   c     走哪條連線
#   lo    最早可出發時間
#   hi    最晚可出發時間（在 [lo, hi] 之間任何時間出發都可行）
#   pred  前一跳的 Label（第一跳是 None）
# 存區間而不是單一時間，是因為 Buffer 隨時間變：早出發可能爆，晚一點反而可以。
Label = namedtuple("Label", "c lo hi pred")


# ---------------------------------------------------------------------------
# 區間集合的小工具：區間集合以 [(a, b), ...] 表示
# ---------------------------------------------------------------------------

def subtract_open(parts, x, y):
    """從閉區間集合 parts 扣掉開區間 (x, y)（x、y 本身保留）。

    例：[(105, 150)] 扣掉 (110, 130) → [(105, 110), (130, 150)]
    """
    out = []
    for a, b in parts:
        if y <= a or x >= b:          # 沒有重疊：整段保留
            out.append((a, b))
            continue
        if a <= x:                    # 左邊剩一段
            out.append((a, x))
        if y <= b:                    # 右邊剩一段
            out.append((y, b))
    return out


def minus(parts, done):
    """從 parts 扣掉已經到過的區間 done（done 已排序、不重疊）。

    用在 insert：同一條連線，已經放進佇列的出發時間不再放第二次。
    例：已有 [(100, 130)]，新來 [(120, 140)] → 只剩 [(130, 140)]
    """
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
    """把重疊或相接的區間合併。例：[(100, 110), (110, 120)] → [(100, 120)]"""
    out = []
    for a, b in sorted(parts):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


# ---------------------------------------------------------------------------
# 第一關：連線限制
# ---------------------------------------------------------------------------

def candidate_range(P, c, head):
    """Algorithm 3：連線 c 的可出發時間集合（還沒看 Buffer）。

    head  前一跳允許的最早出發時間（第一跳是產生時間 g）

    lo = max(連線開始, head)
    hi = min(連線結束 − 傳輸時間, 期限 − 傳輸時間 − 傳播延遲)
    再對每筆預約 (x, y) 扣掉開區間 (x − d, y)：
        新包在 s 出發會占用 [s, s + d]，和 (x, y) 重疊的條件是 x − d < s < y。

    例：連線 100～160、速率 2、包 20 MB（d = 10）、head = 105、預約 (120, 130)
        lo = 105、hi = 150，扣掉 (110, 130) → [(105, 110), (130, 150)]
    """
    d = P.S / c.r
    lo, hi = max(c.a, head), min(c.b - d, P.T - d - c.d)
    if lo > hi:
        return []
    parts = [(lo, hi)]
    for x, y in c.F:
        parts = subtract_open(parts, x - d, y)
    return parts


# ---------------------------------------------------------------------------
# 細緻檢查（三個 filter 共用）
# ---------------------------------------------------------------------------

def solve_region(P, lo, hi, bps, feas, vals):
    """在 [lo, hi] 找出所有可行的出發時間 s。

    bps        切點：s 移動到這些位置時，某個檢查點會碰到 O_n 的變化點
    feas(s)    用 validate.py 的規則直接判斷 s 是否可行（給切點用）
    vals(s, m) 這一段的各檢查點的「合計水位」，m 是段中點，用來決定
               這一段內有哪些舊變化點落在停留期間

    步驟：
    1. 用切點把 [lo, hi] 切成好幾段。
    2. 每個切點本身用 feas 直接檢查（切點上可能有跳變，要用原規則確認）。
    3. 每一段內，每個檢查點的合計水位都是 s 的一次式。
       取 1/3 點 e、2/3 點 g 各算一次，得到斜率 k。
       （在段內部取點，才保證落在同一條直線上，避開端點的跳變或轉彎。）
    4. 解 v(e) + k × (s − e) ≤ M：
           k > 0 → 得到上界 H
           k < 0 → 得到下界 L
           k = 0 → 值超過 M 就整段不行
    5. 所有可行的點和小段合併。

    例（第 4 章）：在 t = 120 的合計 = 10 + (130 − s2) = 140 − s2，k = −1，
        解 140 − s2 ≤ 15 得 s2 ≥ 125。
    """
    pts = sorted({lo, hi} | {b for b in bps if lo < b < hi})
    res = [(p, p) for p in pts if feas(p)]                 # 步驟 2
    for p, q in zip(pts, pts[1:]):                          # 每一段 (p, q)
        e, g, m = p + (q - p) / 3, p + 2 * (q - p) / 3, (p + q) / 2
        L, H, ok = p, q, True
        for va, vb in zip(vals(e, m), vals(g, m)):          # 每個檢查點
            k = (vb - va) / (g - e)                         # 步驟 3：斜率
            if k == 0:
                if va > P.M:
                    ok = False
                    break
            elif k > 0:
                H = min(H, e + (P.M - va) / k)              # 上界
            else:
                L = max(L, e + (P.M - va) / k)              # 下界
        if ok and L <= H:
            res.append((L, H))
    return merge(res)                                       # 步驟 5


# ---------------------------------------------------------------------------
# 第二關：Buffer 篩選。每個都是「先快速檢查，不行再細緻檢查」
# ---------------------------------------------------------------------------

def source_filter(P, c, parts):
    """來源：從 g 起整包占著，在 s 開始送，送的時候慢慢釋放。

    快速檢查：peak(g, hi + d) + S ≤ M
        視窗 [g, hi + d] 是這包在來源上「最多」會停留的範圍。
        假設整包一直疊在最高點上都不爆，那任何出發時間都不爆。
    """
    O = P.O.get(P.src, Curve())
    d = P.S / c.r
    out = []
    for lo, hi in parts:
        if O.peak(P.g, hi + d) + P.S <= P.M:        # 快速檢查通過：整段保留
            out.append((lo, hi))
            continue
        verts = O.between(P.g, hi + d)

        def vals(s, m):
            """出發時間為 s 時，各檢查點的合計水位。"""
            res = [O.right(P.g) + P.S, O.top(s) + P.S]          # g 與 s：整包都在
            for x in O.between(P.g, m + d):
                res.append(O.top(x) + P.S - ramp(x, s, s + d, P.S))  # 送出中
            return res

        # 切點：s 碰到舊變化點 x（開始送），或 s + d 碰到 x（送完）
        bps = [x for x in verts] + [x - d for x in verts]
        out += solve_region(P, lo, hi, bps, lambda s: source_ok(P, c, s), vals)
    return out


def destination_filter(P, c, parts):
    """目的地：只收不送，整包收完的瞬間交付。

    快速檢查：peak(lo + 延遲, hi + 延遲 + 傳輸時間) + S ≤ M
    """
    O = P.O.get(P.dst, Curve())
    if not O.ts:                                    # 目的地完全沒有占用
        return parts if P.S <= P.M else []
    d = P.S / c.r
    out = []
    for lo, hi in parts:
        if O.peak(lo + c.d, hi + c.d + d) + P.S <= P.M:
            out.append((lo, hi))
            continue
        verts = O.between(lo + c.d, hi + c.d + d)

        def vals(s, m):
            h, A = s + c.d, s + c.d + d             # 開始收、收完
            res = [O.left(A) + P.S]                 # 收完前一瞬間：整包
            for x in O.between(m + c.d, m + c.d + d):
                res.append(O.top(x) + ramp(x, h, A, P.S))   # 收的過程中
            return res

        # 切點：開始收 h 或收完 A 碰到舊變化點 x
        bps = [x - c.d for x in verts] + [x - c.d - d for x in verts]
        out += solve_region(P, lo, hi, bps, lambda s: destination_ok(P, c, s), vals)
    return out


def buffer_filter(P, parts, L1, c2):
    """Algorithm 4：中繼節點的 Buffer。

    變數是「下一跳 c2 的出發時間 s2」。
    對每個 s2，前一跳只試最晚的 s1* = min(L1.hi, s2 − dl − lag)：
        s2 固定時，s1 越晚，包在中繼停留越短、占用越少。
        最晚的都不行，更早的也不會行。
        若 s1* < L1.lo，表示前一跳趕不上，這個 s2 不可行。

    快速檢查的視窗：[L1.lo + dl, hi + d2]
        最早開始收（前一跳最早出發 + 延遲）到最晚送完（這一跳最晚出發 + 傳輸時間）。
    """
    c1 = L1.c
    n = c1.v                                        # 中繼節點
    O = P.O.get(n, Curve())
    d1, d2, dl = P.S / c1.r, P.S / c2.r, c1.d       # 收的時間、送的時間、前一跳延遲
    gap = lag(P, c1, c2)
    clamp = L1.hi + dl + gap                        # s2 超過這裡，s1* 就被 L1.hi 卡住
    out = []

    def star(s):
        """s2 = s 時的 s1*；趕不上就回傳 None。"""
        u = s - dl - gap
        return None if u < L1.lo else min(L1.hi, u)

    def feas(s):
        k = star(s)
        return k is not None and relay_ok(P, c1, k, c2, s)

    for lo, hi in parts:
        if O.peak(L1.lo + dl, hi + d2) + P.S <= P.M:    # 快速檢查
            out.append((lo, hi))
            continue

        def vals(s, m):
            """s2 = s 時各檢查點的合計水位。"""
            k = star(s)
            h, A, f = k + dl, k + dl + d1, s + d2       # 開始收、收完、送完
            own = lambda x: ramp(x, h, A, P.S) - ramp(x, s, f, P.S)   # 已收 − 已送
            hm = star(m) + dl
            res = [O.top(A) + own(A), O.top(s) + own(s)]   # 收完、開始送這兩刻
            for x in O.between(hm, m + d2):
                res.append(O.top(x) + own(x))           # 停留期間的舊變化點
            return res

        verts = O.between(L1.lo + dl, hi + d2)
        # 新包的轉折 h = s − gap、A = s − gap + d1、s、f = s + d2 碰到 O 的變化點 x
        # clamp 之後 h、A 固定；cut-through 時 s 越過固定的 A，own(A)、own(s) 會折彎
        bps = [clamp, L1.hi + dl + d1]
        for x in verts:
            bps += [x, x - d2, x + gap, x + gap - d1]
        out += solve_region(P, lo, hi, bps, feas, vals)
    return merge(out)


# ---------------------------------------------------------------------------
# 搜尋
# ---------------------------------------------------------------------------

def path_nodes(P, L):
    """Label L 這條路徑已經過的節點：來源，加上每一跳的終點。

    例：A →(c1) B →(c2) C 的 Label → {A, B, C}
    """
    nodes = {P.src}
    while L is not None:
        nodes.add(L.c.v)
        L = L.pred
    return nodes


def search(P):
    """Algorithm 2。回傳到達目的地的 Label，找不到回傳 None。

    和 Dijkstra 一樣用優先佇列，每次取出「最早到達」的 Label；
    第一個取出的到達目的地的 Label，就是最早到達。

    路徑不重複經過同一節點（2026-11-23 使用者決定）。原因：邊收邊轉時，
    同一包繞回同一節點，兩次停留可能在時間上重疊，檢查會少算自己的占用。
    去重 reached 仍以連線為單位。
    """
    out = out_index(P.cs)
    Q, tick, reached = [], 0, {}        # tick：同分時維持放入順序

    def insert(c, parts, pred):
        """去重後把新的 Label 放進佇列。

        reached[連線] 記錄這條連線已經放過的出發區間，只保留新的部分。
        因為佇列依最早到達取出，先放進去的那段不會比較晚。
        """
        nonlocal tick
        done = reached.get(c.id, [])
        new = merge(minus(parts, done))
        if not new:
            return
        reached[c.id] = merge(done + new)
        for a, b in new:
            tick += 1
            # 排序依據：以最早出發 a 計算的到達時間 = a + 傳輸時間 + 延遲
            heapq.heappush(Q, (a + P.S / c.r + c.d, tick, Label(c, a, b, pred)))

    if P.S > P.M:                       # 包比 Buffer 還大，不可能送
        return None

    # 第一跳：從來源出去的每條連線
    for c in out.get(P.src, []):
        parts = source_filter(P, c, candidate_range(P, c, P.g))
        if c.v == P.dst:                # 一跳就到
            parts = destination_filter(P, c, parts)
        insert(c, parts, None)

    while Q:
        _, _, L1 = heapq.heappop(Q)     # 取出最早到達的
        if L1.c.v == P.dst:             # 已到目的地：這就是最早的
            return L1
        visited = path_nodes(P, L1)
        # 往下一跳展開：從 L1 到達的節點出去的每條連線
        for c2 in out.get(L1.c.v, []):
            if c2.v in visited:          # 不重複經過同一節點（2026-11-23 使用者決定）
                continue
            head = L1.lo + L1.c.d + lag(P, L1.c, c2)    # 下一跳最早可出發
            parts = candidate_range(P, c2, head)
            if not parts:
                continue
            parts = buffer_filter(P, parts, L1, c2)
            if c2.v == P.dst:
                parts = destination_filter(P, c2, parts)
            insert(c2, parts, L1)
    return None


# ---------------------------------------------------------------------------
# 回推與對外介面
# ---------------------------------------------------------------------------

def backtrack(P, goal):
    """Algorithm 6：從終點回推每一跳的出發時間。

    最後一跳取最早（lo），因為它決定到達時間。
    往前每一跳取「趕得上下一跳的最晚出發」：
        k = min(前一跳 hi, 下一跳出發 − 延遲 − lag)
    越晚出發，包在中繼停留越短、占用越少。

    例（第 4 章，收完才轉）：最後一跳 s2 = 125 → s1 = 125 − 0 − 10 = 115。
    """
    L, s = goal, goal.lo
    sch = [(L.c, s)]
    while L.pred is not None:
        q = L.pred
        k = min(q.hi, s - q.c.d - lag(P, q.c, L.c))
        sch.insert(0, (q.c, k))
        L, s = q, k
    return sch


def plan(P):
    """對外介面：回傳排程 [(連線, 出發時間), ...]，找不到回傳 None。"""
    goal = search(P)
    return backtrack(P, goal) if goal else None
