# 核心資料與占用模型：分段線性、逐 byte、精確有理數及驗證後預約更新。
"""Data, exact rational arithmetic, and proposed-side reservation representation."""
from fractions import Fraction as F
from copy import deepcopy


# 用十進位字串建立 Fraction，避免二進位浮點誤差改變邊界判別。
def number(x):
    return F(str(x))


# 複製案例並統一數值型別；避免改到呼叫端原始設定。
def normalize(case):
    case = deepcopy(case)
    for c in case['contacts']:
        for k in ('start', 'end', 'rate', 'delay', 'quota'):
            c[k] = number(c[k])
    for b in case['bundles']:
        b['g'], b['size'] = number(b['g']), number(b['size'])
    case['buffers'] = {v: number(m) for v, m in case['buffers'].items()}
    case['delta'], case['horizon'] = number(case.get('delta', 1)), number(case['horizon'])
    case['background'] = {
        v: [[[number(x) for x in seg] for seg in curve] for curve in curves]
        for v, curves in case.get('background', {}).items()}
    return case


# 檢查正速率、非負延遲、容量範圍與格點對齊；不偷偷四捨五入。
def validate_input(case, b):
    if case['delta'] <= 0 or b['size'] <= 0 or b['g'] > case['horizon']:
        raise ValueError('INVALID_INPUT: grid, size or horizon')
    if b['source'] not in case['buffers'] or b['dest'] not in case['buffers']:
        raise ValueError('INVALID_INPUT: bundle node')
    seen = set()
    for c in case['contacts']:
        if c['id'] in seen or c['u'] == c['v']:
            raise ValueError('INVALID_INPUT: duplicate contact or self-loop')
        seen.add(c['id'])
        if c['rate'] <= 0 or c['delay'] < 0 or c['start'] >= c['end']:
            raise ValueError('INVALID_INPUT: contact')
        if not 0 <= c['quota'] <= c['rate']*(c['end']-c['start']):
            raise ValueError('INVALID_INPUT: quota')
        for t in (c['start'], c['end'], c['delay'], b['size']/c['rate']):
            if (t/case['delta']).denominator != 1:
                raise ValueError('INVALID_INPUT: not aligned to declared grid')
    if (b['g']/case['delta']).denominator != 1:
        raise ValueError('INVALID_INPUT: release not on grid')


# 求同一次節點停留的曲線值；相鄰線段交點取最大，不重複相加。
def curve_value(curve, t):
    # Adjacent pieces describe ONE curve: never sum them twice at a join.
    values = [y0 if lo == hi else y0+(y1-y0)*(t-lo)/(hi-lo)
              for lo, hi, y0, y1 in curve if lo <= t <= hi]
    return max(values, default=F(0))


# 加總該節點所有已接受曲線在 t 的占用量；不包含其他候選 Label。
def occupancy(background, node, t):
    return sum((curve_value(c, t) for c in background.get(node, [])), F(0))


# 在新增曲線和既有曲線的所有相關折點求峰值，不只檢查格點或起訖。
def peak(background, node, curve):
    # 分段線性總和只可能在折點／邊界取得更大值；同時事件沿用峰值約定。
    lo, hi = curve[0][0], curve[-1][1]
    points = {p for seg in curve for p in seg[:2]}
    for other in background.get(node, []):
        points.update(p for seg in other for p in seg[:2] if lo <= p <= hi)
    values = [(occupancy(background, node, t)+curve_value(curve, t), t)
              for t in sorted(points)]
    return max(values, key=lambda item: item[0])


# 依完整路徑建立每次停留的接收、等待與送出曲線，含交付前峰值。
def route_curves(case, b, hops):
    """One curve for each visit; source / destination retain peak event points."""
    contacts = {c['id']: c for c in case['contacts']}
    out = {}
    S = b['size']
    if not hops:
        return {b['source']: [[[b['g'], b['g'], S, S]]]}
    arrivals, rx_starts = [], []
    for cid, s in hops:
        c = contacts[cid]
        rx_starts.append(s+c['delay'])
        arrivals.append(s+S/c['rate']+c['delay'])
    for i in range(len(hops)+1):
        node = b['source'] if i == 0 else contacts[hops[i-1][0]]['v']
        full = b['g'] if i == 0 else arrivals[i-1]
        pieces = []
        if i > 0:
            pieces.append([rx_starts[i-1], full, F(0), S])
        if i < len(hops):
            cid, s = hops[i]
            pieces.extend([[full, s, S, S], [s, s+S/contacts[cid]['rate'], S, F(0)]])
        out.setdefault(node, []).append(pieces)
    return out


# 建立新的容量與占用狀態；路徑重複使用同 Contact 時逐次扣量。
def commit(case, quota, background, b, hops):
    # 先深複製再更新，讓 runner 可以在接受新狀態前與獨立實作核對。
    new_q, new_o = deepcopy(quota), deepcopy(background)
    for cid, _ in hops:
        new_q[cid] -= b['size']
    for v, curves in route_curves(case, b, hops).items():
        new_o.setdefault(v, []).extend(curves)
    return new_q, new_o


# 遞迴把 Fraction、tuple 等轉成 JSON 可保存的值；不是運算時取近似值。
def jsonable(obj):
    if isinstance(obj, F):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(x) for x in obj]
    return obj
