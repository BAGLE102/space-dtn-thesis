"""重寫練習：把每個 TODO 自己寫出來。

規則
- 一次只做一關，寫完就跑：python3 check.py 關卡編號（在 src/practice 底下）
- 卡住先看說明裡的例子，用手算一次；還是不行再去看 src/algorithm/ 的答案。
- 全部用 Fraction（分數）運算，不要用浮點數。

關卡
  1  ramp、lag
  2  Curve：left、right、top、between、peak
  3  Curve.add（兩條曲線相加）
  4  規則：stay_ok、source_ok、relay_ok、destination_ok、hop_ok、validate
  5  區間：subtract_open、merge、candidate_range
  6  commit（排定後寫入 F 與 O_n）
  7  簡單版搜尋 plan_simple：在格點上試出發時間（概念最直接，先求對）
  8  正式版搜尋 plan：區間 Label + Buffer 篩選（最難，前面都過了再做）
"""
import heapq
from collections import namedtuple
from fractions import Fraction as Fr

# ---------------------------------------------------------------------------
# 已經給好的資料結構（不用寫）
# ---------------------------------------------------------------------------

# 連線：從 u 到 v，a～b 開放，速率 r，傳播延遲 d，已預約時段 F（例如 ((120, 130),)）
Contact = namedtuple("Contact", "id u v a b r d F")

# 問題：連線、來源、目的地、產生時間 g、大小 S、Buffer 上限 M、
#       各節點占用 O = {節點: Curve}、期限 T、ct = 是否邊收邊轉
Problem = namedtuple("Problem", "cs src dst g S M O T ct", defaults=(False,))

# 搜尋狀態：走連線 c，可在 [lo, hi] 出發，前一跳 pred
Label = namedtuple("Label", "c lo hi pred")


def out_index(cs):
    """{節點: [從這個節點出去的連線]}。已給好。"""
    out = {}
    for c in cs:
        out.setdefault(c.u, []).append(c)
    return out


def arrival(P, sch):
    """排程的到達時間。已給好。sch = [(連線, 出發時間), ...]"""
    c, s = sch[-1]
    return s + P.S / c.r + c.d


# ===========================================================================
# 關卡 1：ramp、lag
# ===========================================================================

def ramp(t, a, b, S):
    """從 a 到 b 由 0 直線升到 S，回傳 t 時刻的值。

    t ≤ a 回傳 0；t ≥ b 回傳 S；中間直線內插。
    例：ramp(120, 115, 125, 10) = 5；ramp(130, 115, 125, 10) = 10
    """
    raise NotImplementedError("TODO 關卡 1")


def lag(P, c1, c2):
    """前一跳出發到下一跳最早出發的間隔（不含傳播延遲）。

    收完才轉（P.ct 為 False）：S / r1
    邊收邊轉（P.ct 為 True）：max(0, S/r1 − S/r2)
    例：S = 20、r1 = 2、r2 = 4 → 收完才轉 10，邊收邊轉 5
    """
    raise NotImplementedError("TODO 關卡 1")


# ===========================================================================
# 關卡 2、3：Curve
# ===========================================================================

class Curve:
    """O_n：ts 變化點時刻（由小到大），ls 左極限，rs 右極限。

    兩點之間：從前一點的 rs 直線連到後一點的 ls。
    第一點之前：值是 ls[0]。最後一點之後：值是 rs[-1]。沒有任何點：值是 0。
    例：ts [100, 110, 120, 130]、ls = rs = [0, 10, 10, 0]
    """

    def __init__(self, ts=(), ls=(), rs=()):
        self.ts, self.ls, self.rs = list(ts), list(ls), list(rs)

    def left(self, t):
        """t 的左極限。t 剛好是變化點時回傳該點的 ls。例：上面的例子 left(125) = 5

        提示：bisect.bisect_left(self.ts, t) 找到第一個 ≥ t 的位置 i，
        再分成「沒有點／在最後一點之後／剛好是變化點或在第一點之前／在兩點之間」。
        """
        raise NotImplementedError("TODO 關卡 2")

    def right(self, t):
        """t 的右極限。t 剛好是變化點時回傳該點的 rs。"""
        raise NotImplementedError("TODO 關卡 2")

    def top(self, t):
        """max(left(t), right(t))。"""
        raise NotImplementedError("TODO 關卡 2")

    def between(self, a, b):
        """嚴格落在 (a, b) 之內的變化點時刻清單（不含 a、b）。a ≥ b 時回傳空清單。

        例：between(100, 130) = [110, 120]
        """
        raise NotImplementedError("TODO 關卡 2")

    def peak(self, a, b):
        """[a, b] 內的最高值：a、b 兩端的 top，加上中間變化點的 top，取最大。

        例：peak(100, 130) = 10，peak(112, 118) = 10，peak(125, 140) = 5
        """
        raise NotImplementedError("TODO 關卡 2")

    def add(self, o):
        """回傳兩條曲線相加的新 Curve。

        變化點取聯集並排序；每個點的 ls 相加、rs 相加。
        （原程式還會刪掉共線的多餘點，這裡可以不做，檢查只比對數值。）
        """
        raise NotImplementedError("TODO 關卡 3")


# ===========================================================================
# 關卡 4：規則
# ===========================================================================

def stay_ok(O, M, start, end, own, own_end, pts=()):
    """檢查 start 到 end 之間每一刻 O(t) + own(t) ≤ M。

    要檢查的時刻：
      start：只在 own(start) > 0 時檢查 O.right(start) + own(start) ≤ M
      end  ：只在 own_end > 0 時檢查 O.left(end) + own_end ≤ M
      pts 與 O 在 (start, end) 內的變化點 t：只在 own(t) > 0 時檢查 O.top(t) + own(t) ≤ M
    """
    raise NotImplementedError("TODO 關卡 4")


def source_ok(P, c, s):
    """來源：g 起整包 S 占著，在 s 開始送、f = s + S/r 送完。

    own(t) = S − ramp(t, s, f, S)，檢查區間 [g, f]，own_end = 0，pts = [s]
    節點的占用：P.O.get(P.src, Curve())
    """
    raise NotImplementedError("TODO 關卡 4")


def relay_ok(P, c1, s1, c2, s2):
    """中繼 c1.v：h = s1 + c1.d、A = h + S/r1、f = s2 + S/r2。

    轉送條件：收完才轉 s2 ≥ A；邊收邊轉 s2 ≥ h 且 f ≥ A。不符合回傳 False。
    Buffer：own(t) = ramp(t, h, A, S) − ramp(t, s2, f, S)，檢查 [h, f]，own_end = 0，pts = [A, s2]
    例（第 4 章例子）：s1 = 115、s2 = 125 → True；s1 = 114、s2 = 124 → False
    """
    raise NotImplementedError("TODO 關卡 4")


def destination_ok(P, c, s):
    """目的地：h = s + c.d、A = h + S/r。own(t) = ramp(t, h, A, S)，檢查 [h, A]，own_end = S。"""
    raise NotImplementedError("TODO 關卡 4")


def hop_ok(P, c, s):
    """單一跳：s ≥ c.a；s + S/r ≤ c.b；s + S/r + c.d ≤ T；不和 F 裡任何 (x, y) 重疊。

    重疊的條件：s < y 且 x < s + S/r
    """
    raise NotImplementedError("TODO 關卡 4")


def validate(P, sch):
    """整條排程合法嗎？

    1. 非空、第一跳從 src 出發、最後一跳到 dst、第一跳出發 ≥ g
    2. 相鄰兩跳接得起來（前一跳的 v = 下一跳的 u），且不重複經過同一節點
       （src 與每一跳的 v 都不能重複）
    3. 每一跳 hop_ok
    4. 第一跳 source_ok、最後一跳 destination_ok
    5. 每對相鄰的跳 relay_ok
    """
    raise NotImplementedError("TODO 關卡 4")


# ===========================================================================
# 關卡 5：區間
# ===========================================================================

def subtract_open(parts, x, y):
    """從閉區間清單 parts 扣掉開區間 (x, y)。

    例：[(105, 150)] 扣掉 (110, 130) → [(105, 110), (130, 150)]
    """
    raise NotImplementedError("TODO 關卡 5")


def merge(parts):
    """排序後把重疊或相接的區間合併。例：[(110, 120), (100, 110)] → [(100, 120)]"""
    raise NotImplementedError("TODO 關卡 5")


def candidate_range(P, c, head):
    """連線 c 的可出發時間（還沒看 Buffer）。

    d = S/r；lo = max(c.a, head)；hi = min(c.b − d, T − d − c.d)；lo > hi 回傳 []
    對每筆預約 (x, y) 扣掉開區間 (x − d, y)。
    例：連線 100～160、r = 2、S = 20、head = 105、F = ((120, 130),) → [(105, 110), (130, 150)]
    """
    raise NotImplementedError("TODO 關卡 5")


# ===========================================================================
# 關卡 6：commit
# ===========================================================================

def commit(P, sch):
    """回傳新的 Problem：每一跳的 (s, s + S/r) 加進該連線的 F；這包的占用加進 O。

    來源：g < s0 時 Curve([g, s0, f0], [0, S, 0], [S, S, 0])；否則 Curve([s0, f0], [0, 0], [S, 0])
    中繼：邊收邊轉且 s2 < A → 在 sorted({h, A, s2, f}) 算 ramp(x,h,A,S) − ramp(x,s2,f,S)，ls = rs = 這些值
          A < s2 → Curve([h, A, s2, f], [0, S, S, 0], [0, S, S, 0])
          否則   → Curve([h, A, f], [0, S, 0], [0, S, 0])
    目的地：Curve([h, A], [0, S], [0, 0])
    加進節點：O[n] = O[n].add(cv) if n in O else cv（不要改到原本的 P.O，先複製 dict）
    更新連線：P._replace(cs=[c._replace(F=tuple(新的 F)) ...], O=新的 O)
    """
    raise NotImplementedError("TODO 關卡 6")


# ===========================================================================
# 關卡 7：簡單版搜尋（格點）
# ===========================================================================

def plan_simple(P, grid=Fr(1, 16)):
    """在格點上試每條連線的出發時間，找最早到達的合法排程。

    概念最直接的版本：出發時間只試 grid 的倍數。
    做法提示（類似 Dijkstra）：
      1. 狀態是 (連線, 出發時間 s)。
      2. 起點：從 src 出去的連線，s 為格點、s ≥ g、hop_ok、source_ok。
      3. 展開：從 (c, s) 接 c.v 出去的 c2，試格點 s2，要 hop_ok 且 relay_ok(P, c, s, c2, s2)。
         路徑不能重複經過同一節點，所以狀態要記住已經過的節點。
      4. 終點：c.v == dst 且 destination_ok，到達時間 = s + S/r + c.d。
      5. 回傳最早到達的排程 [(連線, 出發), ...]；沒有就回傳 None。
    格點時間可以這樣列：從 ceil(c.a / grid) × grid 開始，每次加 grid，直到傳不完為止。
    """
    raise NotImplementedError("TODO 關卡 7")


# ===========================================================================
# 關卡 8：正式版搜尋（區間 Label）
# ===========================================================================

def plan(P):
    """正式版：區間 Label 搜尋 + 回推。回傳排程或 None。

    建議順序（每一步都可以先用簡單方法求對，再換成快的方法）：
      1. 先寫 search：優先佇列存 (lo + S/r + d, 計數, Label)，取出到 dst 就結束。
         第一跳：candidate_range(P, c, g)；下一跳：head = L1.lo + L1.c.d + lag。
         展開時跳過 c2.v 已在路徑上的連線（沿 pred 往回找已經過的節點）。
      2. 寫 backtrack：最後一跳取 lo；往前 k = min(q.hi, s − q.c.d − lag)。
      3. Buffer 篩選（來源、中繼、目的地）：
         先用「快速檢查」peak(視窗) + S ≤ M，通過就整段保留；
         不通過時，第一版可以先在區間內用格點逐一試 relay_ok 等規則（慢但對），
         最後再改成 solve_region：用變化點切段，每段解一次式不等式。
      4. 去重：每條連線記錄已放過的區間，只放新的部分。
    """
    raise NotImplementedError("TODO 關卡 8")
