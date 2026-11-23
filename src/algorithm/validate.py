"""規則本身：什麼樣的排程是合法的，以及排定後怎麼寫入網路狀態。

這個檔案「不呼叫任何搜尋或篩選函式」。用途有兩個：
1. 搜尋找到排程後，用這裡的規則獨立再檢查一次（回放），搜尋寫錯會被抓到。
2. 搜尋的細緻檢查在「切點」上，也直接用這裡的 *_ok 判斷。

符號（中繼節點）：
    s1  前一跳出發時間          h  = s1 + d1    開始收
    s2  下一跳出發時間          A  = h + S/r1   收完
                                f  = s2 + S/r2  送完

占用檢查取停留期間的最高值（上確界）。資料在目的地整包收完的瞬間 A 交付並離開。

本檔案與 src/experiments/dtn_validation/dtn/validate.py 的邏輯完全相同，只加了註解。
"""
from fractions import Fraction as Fr
from .model import Curve, ramp


# ---------------------------------------------------------------------------
# Buffer 檢查的共用核心
# ---------------------------------------------------------------------------

def stay_ok(O, M, start, end, own, own_end, pts=()):
    """檢查從 start 到 end，每一刻 O(t) + own(t) ≤ M。

    O        節點原本的占用曲線（前面的包）
    own(t)   這一包在這個節點 t 時刻的量
    own_end  這一包在 end 的左極限
    pts      這一包自己的變化點（例如收完 A、開始送 s2）

    只檢查這些時刻（兩點之間是直線，最大值一定在端點）：
        起點 start：用 O 的右極限
        終點 end：用 O 的左極限
        中間：這一包的變化點 pts，加上 O 在 (start, end) 內的變化點

    已知限制：own 為 0 的時刻不檢查。只有在背景占用本身就超過 M 時有影響
    （cut-through 驗證的案例 2663），是否收緊尚未決定。
    """
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


# ---------------------------------------------------------------------------
# 三種節點的 Buffer 規則
# ---------------------------------------------------------------------------

def source_ok(P, c, s):
    """來源：從產生時間 g 起就整包占著，在 s 開始送，送的時候慢慢降到 0。

    例：g = 100、s = 110、S = 10、r = 1
        100～110 一直是 10，110～120 從 10 降到 0。
    """
    d = P.S / c.r
    f = s + d                                     # 送完的時間
    own = lambda t: P.S - ramp(t, s, f, P.S)      # 整包 − 已送出
    return stay_ok(P.O.get(P.src, Curve()), P.M, P.g, f, own, Fr(0), [s])


def relay_ok(P, c1, s1, c2, s2):
    """中繼：c1 在 s1 出發送進來，c2 在 s2 出發送出去。

    先檢查轉送條件，再檢查 Buffer。
        收完才轉：s2 ≥ A（整包收完才能送）
        邊收邊轉：s2 ≥ h（第一個 byte 到了才能送）而且 f ≥ A（送完不能早於收完）
    """
    d1, d2 = P.S / c1.r, P.S / c2.r
    h = s1 + c1.d                                 # 開始收
    A = h + d1                                    # 收完
    f = s2 + d2                                   # 送完
    if P.ct:
        if s2 < h or f < A:          # 邊收邊轉：已開始收，且送不能比收快
            return False
    elif s2 < A:                     # 收完才轉：收完才送
        return False
    # 這包在中繼的量 = 已收 − 已送
    own = lambda t: ramp(t, h, A, P.S) - ramp(t, s2, f, P.S)
    return stay_ok(P.O.get(c1.v, Curve()), P.M, h, f, own, Fr(0), [A, s2])


def destination_ok(P, c, s):
    """目的地：只收不送，收的期間占空間，在 A（整包收完）那一刻交付、歸零。"""
    d = P.S / c.r
    h = s + c.d                                   # 開始收
    A = h + d                                     # 收完
    own = lambda t: ramp(t, h, A, P.S)
    # own_end = S：終點 A 的左極限是整包（交付前一瞬間還在）
    return stay_ok(P.O.get(P.dst, Curve()), P.M, h, A, own, P.S)


# ---------------------------------------------------------------------------
# 連線規則
# ---------------------------------------------------------------------------

def hop_ok(P, c, s):
    """單一跳在 s 出發是否合法：

    1. s ≥ 連線開始
    2. s + 傳輸時間 ≤ 連線結束（要在連線關掉前傳完）
    3. 到達時間 ≤ 期限 T
    4. 不和已預約的時段 (x, y) 重疊：s < y 且 x < s + d 就是重疊
    """
    d = P.S / c.r
    if s < c.a or s + d > c.b or s + d + c.d > P.T:
        return False
    return not any(s < y and x < s + d for x, y in c.F)


# ---------------------------------------------------------------------------
# 整條排程的檢查
# ---------------------------------------------------------------------------

def validate(P, sch):
    """獨立檢查整條排程 sch = [(連線, 出發時間), ...] 是否合法。

    1. 從來源出發、到目的地結束、不早於產生時間 g
    2. 每一跳接得起來（前一跳的終點 = 下一跳的起點）
    3. 每一跳 hop_ok
    4. 來源、目的地的 Buffer
    5. 每個中繼的轉送條件與 Buffer
    """
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


# ---------------------------------------------------------------------------
# 排定後寫入網路狀態
# ---------------------------------------------------------------------------

def commit(P, sch):
    """把排定的包寫進網路狀態，回傳新的 Problem（原本的不改）。

    寫兩樣東西：
    1. 每一跳的傳輸時段 (s, s + S/r) 加進那條連線的預約 F
    2. 這包在每個節點的占用加進該節點的 O_n

    下一包就在這個新狀態上規劃。
    """
    F = {c.id: list(c.F) for c in P.cs}
    O = dict(P.O)
    S = P.S

    def put(n, cv):
        """把曲線 cv 加到節點 n 的 O_n。"""
        O[n] = O[n].add(cv) if n in O else cv

    # 1. 連線預約
    for c, s in sch:
        F[c.id].append((s, s + S / c.r))

    # 2a. 來源：g 起整包占著，s0 開始送、f0 送完
    c0, s0 = sch[0]
    f0 = s0 + S / c0.r
    if P.g < s0:
        # 例：g = 100、s0 = 110、f0 = 120 → ts [100, 110, 120]
        #     在 100 從 0 跳到 S（ls 0、rs S），110 前維持 S，110～120 降到 0
        put(P.src, Curve([P.g, s0, f0], [Fr(0), S, Fr(0)], [S, S, Fr(0)]))
    else:
        # 一產生就送：在 s0 跳到 S，馬上開始降
        put(P.src, Curve([s0, f0], [Fr(0), Fr(0)], [S, Fr(0)]))

    # 2b. 中繼：三種形狀
    for (c1, s1), (c2, s2) in zip(sch, sch[1:]):
        h = s1 + c1.d                             # 開始收
        A = h + S / c1.r                          # 收完
        f = s2 + S / c2.r                         # 送完
        if P.ct and s2 < A:
            # 邊收邊轉、收和送重疊：在 h、A、s2、f 算「已收 − 已送」
            # 例：h = 100、A = 110、s2 = 100、f = 110（同速）→ 全部是 0
            ts = sorted({h, A, s2, f})
            vs = [ramp(x, h, A, S) - ramp(x, s2, f, S) for x in ts]
            put(c1.v, Curve(ts, vs, vs))
        elif A < s2:
            # 收完後等一陣子才送：升、持平、降
            # 例：h = 100、A = 110、s2 = 120、f = 130 → [0, 10, 10, 0]
            put(c1.v, Curve([h, A, s2, f], [Fr(0), S, S, Fr(0)], [Fr(0), S, S, Fr(0)]))
        else:
            # 收完馬上送（A = s2）：升到 S 立刻降
            put(c1.v, Curve([h, A, f], [Fr(0), S, Fr(0)], [Fr(0), S, Fr(0)]))

    # 2c. 目的地：h～A 升到 S，在 A 交付歸零（A 的 ls = S、rs = 0）
    c, s = sch[-1]
    h = s + c.d
    A = h + S / c.r
    put(P.dst, Curve([h, A], [Fr(0), S], [Fr(0), Fr(0)]))

    return P._replace(cs=[c._replace(F=tuple(F[c.id])) for c in P.cs], O=O)
