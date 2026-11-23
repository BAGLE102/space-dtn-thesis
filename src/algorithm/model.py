"""資料結構：連線（Contact）、問題（Problem）、Buffer 占用曲線（Curve，即 O_n）。

全部數值用 Fraction（分數）精確計算，沒有浮點誤差，
所以「剛好等於上限」這種邊界不會被誤判。

本檔案與 src/experiments/dtn_validation/dtn/model.py 的邏輯完全相同，只加了註解。
"""
from bisect import bisect_left, bisect_right
from collections import namedtuple
from fractions import Fraction as Fr


# ---------------------------------------------------------------------------
# 連線與問題
# ---------------------------------------------------------------------------

# 一條連線（contact）：
#   id   名稱，例如 "c1"
#   u, v 從節點 u 傳到節點 v
#   a, b 連線開始、結束時間（例：100、150）
#   r    速率 MB/s（例：1）
#   d    傳播延遲，秒（訊號從 u 飛到 v 要的時間）
#   F    已預約的傳輸時段，例如 ((120, 130),)，表示別的包在 120～130 用這條連線
Contact = namedtuple("Contact", "id u v a b r d F")

# 目前要規劃的這一包，加上整個網路的狀態：
#   cs   所有連線（每條連線各自帶著自己的 F）
#   src  來源節點
#   dst  目的地節點
#   g    包產生的時間
#   S    包的大小 MB
#   M    每個節點的 Buffer 上限 MB（目前所有節點同一個值）
#   O    {節點: Curve}，各節點已被前面的包占用的 Buffer（就是 O_n）
#   T    期限，必須在 T 之前送到
#   ct   True = 邊收邊轉（cut-through）；False = 收完才轉（store-and-forward，預設）
Problem = namedtuple("Problem", "cs src dst g S M O T ct", defaults=(False,))


def lag(P, c1, c2):
    """前一跳出發 s1 到下一跳最早出發 s2 的最小間隔（不含傳播延遲）。

    兩種轉送方式在搜尋上的差別，幾乎都集中在這個函式。

    收完才轉：要等整包收完，s2 ≥ s1 + S/r1，間隔 = S/r1。
    邊收邊轉：已開始收就能送，但送完不能早於收完。
              s2 + S/r2 ≥ s1 + S/r1，間隔 = max(0, S/r1 − S/r2)。

    例：S = 20、r1 = 2、r2 = 4
        收完才轉 → 20/2 = 10
        邊收邊轉 → max(0, 10 − 5) = 5（送比收快，要先收 5 秒才開始送）
    """
    d1, d2 = P.S / c1.r, P.S / c2.r
    return max(Fr(0), d1 - d2) if P.ct else d1


# ---------------------------------------------------------------------------
# Curve：節點的 Buffer 占用曲線 O_n
# ---------------------------------------------------------------------------

class Curve:
    """分段直線的 Buffer 占用曲線，只存「變化點」。

    三個清單，長度相同：
        ts  變化點時刻，由小到大
        ls  每個變化點的左極限（剛到這一刻之前的值）
        rs  每個變化點的右極限（剛過這一刻之後的值）

    讀法：
        兩個變化點之間：從前一點的 rs 直線連到後一點的 ls。
        同一點 ls ≠ rs：瞬間跳（例如來源產生一包、目的地交付一包）。
        最後一點之後：維持 rs[-1]。

    例（第 4 章的舊包）：
        ts = [100, 110, 120, 130]
        ls = [0,   10,  10,  0]
        rs = [0,   10,  10,  0]
        表示 100～110 從 0 升到 10，110～120 維持 10，120～130 降到 0。

    兩點之間的斜率 = (ls[i] − rs[i−1]) ÷ (ts[i] − ts[i−1])，就是「流入 − 流出」。
    rate 不另外存，需要時從相鄰兩點算出（只知道淨值，分不出進與出）。
    """
    __slots__ = ("ts", "ls", "rs")

    def __init__(self, ts=(), ls=(), rs=()):
        self.ts, self.ls, self.rs = list(ts), list(ls), list(rs)

    def _between(self, i, t):
        """t 落在 ts[i−1] 和 ts[i] 之間時，用直線內插算出值。

        例：ts = [120, 130]、rs[120] = 10、ls[130] = 0，求 t = 125：
            10 + (0 − 10) × (125 − 120) ÷ (130 − 120) = 5
        """
        x0, y0, x1, y1 = self.ts[i - 1], self.rs[i - 1], self.ts[i], self.ls[i]
        return y0 + (y1 - y0) * (t - x0) / (x1 - x0)

    def left(self, t):
        """t 的左極限（剛到 t 之前的值）。"""
        if not self.ts:                    # 空曲線：完全沒有占用
            return Fr(0)
        i = bisect_left(self.ts, t)        # 二分法：第一個 ≥ t 的變化點位置
        if i == len(self.ts):              # t 在最後一點之後：維持最後的值
            return self.rs[-1]
        if self.ts[i] == t or i == 0:      # t 剛好是變化點，或在第一點之前
            return self.ls[i]
        return self._between(i, t)         # t 在兩點之間：內插

    def right(self, t):
        """t 的右極限（剛過 t 之後的值）。"""
        if not self.ts:
            return Fr(0)
        i = bisect_left(self.ts, t)
        if i == len(self.ts):
            return self.rs[-1]
        if self.ts[i] == t:                # t 剛好是變化點：取右極限
            return self.rs[i]
        if i == 0:                         # t 在第一點之前
            return self.ls[0]
        return self._between(i, t)

    def top(self, t):
        """t 時刻左右極限取大的，保守地當作這一刻的占用。"""
        return max(self.left(t), self.right(t))

    def between(self, a, b):
        """嚴格落在 (a, b) 之內的變化點時刻（不含 a、b 本身）。"""
        return self.ts[bisect_right(self.ts, a):bisect_left(self.ts, b)] if a < b else []

    def peak(self, a, b):
        """[a, b] 內的最高占用。

        直線的最大值一定在端點，所以只要看 a、b 兩端和中間的變化點，
        不用一秒一秒檢查。

        例：上面的舊包，peak(100, 130) = 10，peak(112, 118) = 10。
        """
        vals = [self.top(a), self.top(b)]
        vals += [self.top(x) for x in self.between(a, b)]
        return max(vals)

    def global_peak(self):
        """整條曲線的最高點與發生時刻（實驗統計用）。"""
        if not self.ts:
            return Fr(0), None
        best, when = None, None
        for t, l, r in zip(self.ts, self.ls, self.rs):
            if best is None or max(l, r) > best:
                best, when = max(l, r), t
        return best, when

    def add(self, o):
        """兩條曲線相加，例如把新排定的包加進節點的 O_n。

        做法：變化點取聯集，在每個點上左極限相加、右極限相加，
        最後用 _prune 刪掉多餘的點。
        """
        ts = sorted(set(self.ts) | set(o.ts))
        ls = [self.left(t) + o.left(t) for t in ts]
        rs = [self.right(t) + o.right(t) for t in ts]
        return Curve(*_prune(ts, ls, rs))


def _prune(ts, ls, rs):
    """刪掉「沒有跳變、而且剛好落在前後兩點連線上」的點。

    這種點刪掉後曲線形狀不變。不刪的話，包越多變化點越多，查詢越來越慢。
    例：(100, 0)、(105, 5)、(110, 10) 在同一直線上 → 刪掉 105。
    """
    if len(ts) < 3:
        return ts, ls, rs
    T, L, R = [ts[0]], [ls[0]], [rs[0]]
    for i in range(1, len(ts) - 1):
        if ls[i] == rs[i]:                 # 這一點沒有跳變
            x0, y0, x1, y1 = T[-1], R[-1], ts[i + 1], ls[i + 1]
            # 檢查三點是否共線（交叉相乘，避免除法）
            if (ls[i] - y0) * (x1 - x0) == (y1 - y0) * (ts[i] - x0):
                continue                   # 共線：刪掉
        T.append(ts[i])
        L.append(ls[i])
        R.append(rs[i])
    T.append(ts[-1])
    L.append(ls[-1])
    R.append(rs[-1])
    return T, L, R


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def ramp(t, a, b, S):
    """從 a 到 b 由 0 直線升到 S：時間 t 時「已經傳了多少」。

    例：a = 115、b = 125、S = 10
        ramp(115) = 0、ramp(120) = 5、ramp(125) = 10、ramp(130) = 10

    收包：節點上的量 = ramp(收的時段)
    送包：節點上的量 = S − ramp(送的時段)
    """
    if t <= a:
        return Fr(0)
    if t >= b:
        return S
    return S * (t - a) / (b - a)


def arrival(P, sch):
    """排程的到達時間 = 最後一跳出發 + 傳輸時間 + 傳播延遲。

    sch 是 [(連線, 出發時間), ...]。
    """
    c, s = sch[-1]
    return s + P.S / c.r + c.d


def out_index(cs):
    """建立 {節點: [從這個節點出去的連線]}，搜尋時用來找下一跳。"""
    out = {}
    for c in cs:
        out.setdefault(c.u, []).append(c)
    return out
