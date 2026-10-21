"""核對外部 AI 的固定排程例子；不是新路由演算法或效能實驗。"""

from fractions import Fraction as Q
from pathlib import Path
import json


def curve(points, time):
    """連續分段線性曲線；定義域外沿用端值。"""
    if time <= points[0][0]:
        return points[0][1]
    for (a, x), (b, y) in zip(points, points[1:]):
        if time <= b:
            return x + (y - x) * (time - a) / (b - a)
    return points[-1][1]


def peak(points, start, end, offset, slope):
    """固定排程下總占用為分段線性；檢查端點及曲線轉折點即可。"""
    times = {start, end} | {t for t, _ in points if start <= t <= end}
    return max(curve(points, t) + offset + slope * (t - start) for t in times)


def constant():
    return [(Q(0), Q(0)), (Q(100), Q(0))]


def contact(u, v, start, end, rate=1, delay=0, quota=100):
    return dict(u=u, v=v, start=Q(start), end=Q(end), rate=Q(rate),
                delay=Q(delay), quota=Q(quota))


def check_route(contacts, occupancy, limits, route, size, source, release=0):
    """逐跳核對具體排程，並按原始 contact ID 累計整包容量。"""
    size, arrival = Q(size), Q(release)
    node, used, rows = source, {}, []
    local_ok = True
    for cid, raw_start in route:
        c, start = contacts[cid], Q(raw_start)
        duration = size / c['rate']
        finish, receive = start + duration, start + c['delay']
        new_arrival = finish + c['delay']
        ordered = node == c['u'] and arrival <= start
        window = c['start'] <= start and finish <= c['end']
        if not ordered:
            raise ValueError('This fixed trace is not causally ordered')
        waiting_peak = peak(occupancy[node], arrival, start, size, Q(0))
        sending_peak = peak(occupancy[node], start, finish, size, -c['rate'])
        receiving_peak = peak(occupancy[c['v']], receive, new_arrival, Q(0), c['rate'])
        buffers = (waiting_peak <= limits[node] and sending_peak <= limits[node]
                   and receiving_peak <= limits[c['v']])
        local_ok = local_ok and window and buffers
        used[cid] = used.get(cid, Q(0)) + size
        rows.append(dict(contact=cid, start=str(start), arrival=str(new_arrival),
                         waiting_peak=str(waiting_peak), sending_peak=str(sending_peak),
                         receiving_peak=str(receiving_peak), local_checks=window and buffers))
        arrival, node = new_arrival, c['v']
    excess = {cid: str(value) for cid, value in used.items() if value > contacts[cid]['quota']}
    return dict(arrival=str(arrival), local_checks=local_ok, quota_excess=excess,
                feasible=local_ok and not excess, hops=rows)


def main():
    # 外部 AI 的 N0→N1→N2 例子：驗證給定排程，不宣稱驗證所有連續時間。
    middle = [(Q(t), Q(o)) for t, o in [(0, 0), (20, 0), (30, 10), (40, 10), (50, 0), (100, 0)]]
    cs = {'c1': contact('N0', 'N1', 0, 100), 'c2': contact('N1', 'N2', 60, 100, quota=30)}
    os = {'N0': constant(), 'N1': middle, 'N2': constant()}
    caps = {'N0': Q(100), 'N1': Q(15), 'N2': Q(100)}
    early = check_route(cs, os, caps, [('c1', 0), ('c2', 70)], 10, 'N0')
    late = check_route(cs, os, caps, [('c1', 35), ('c2', 70)], 10, 'N0')
    reception = {str(s): str(peak(middle, Q(s), Q(s + 10), Q(0), Q(1)))
                 for s in [15, 16, 34, 35]}
    assert not early['feasible'] and late['feasible'] and late['arrival'] == '80'
    assert reception == {'15': '15', '16': '16', '34': '16', '35': '15'}

    # 反例：R 是獨立 aggregate quota。節點+持有時段相同仍可能有不同已用容量。
    # U 的整包持有集合 [0,2]∪[5,20]；V 為 [0,3]∪[6,20]。
    os2 = {'X': constant(), 'D': constant(),
           'U': [(Q(t), Q(o)) for t, o in [(0, 0), (2, 0), (3, 1), (4, 1), (5, 0), (20, 0)]],
           'V': [(Q(t), Q(o)) for t, o in [(0, 0), (3, 0), (4, 1), (5, 1), (6, 0), (20, 0)]]}
    cs2 = {'early': contact('X', 'U', 0, 1, quota=1),
           'late': contact('X', 'U', Q(9, 2), Q(11, 2), quota=1),
           'c': contact('U', 'V', 1, 10, quota=1),
           'back': contact('V', 'U', 2, 3, delay=2, quota=1),
           'goal': contact('V', 'D', 7, 8, quota=1)}
    caps2 = {v: Q(1) for v in os2}
    first = [('early', 0), ('c', 1), ('back', 2)]
    second = [('late', Q(9, 2))]
    p1 = check_route(cs2, os2, caps2, first, 1, 'X')
    p2 = check_route(cs2, os2, caps2, second, 1, 'X')
    bad = check_route(cs2, os2, caps2, first + [('c', 5), ('goal', 7)], 1, 'X')
    good = check_route(cs2, os2, caps2, second + [('c', Q(11, 2)), ('goal', 7)], 1, 'X')
    assert p1['feasible'] and p2['feasible'] and p1['arrival'] == '5' and p2['arrival'] == '11/2'
    assert bad['local_checks'] and bad['quota_excess'] == {'c': '2'}
    assert good['feasible'] and good['arrival'] == '8'

    # Rule B 與「先釋放再接納來源資料」不是同一種事件模型。
    # 節點上限1：既有資料在t=1交付釋放，本包也在g=1成為可用。
    # 既有占用：事件前1、後0；本包：事件前0、後1。
    before_total, after_total = Q(1) + Q(0), Q(0) + Q(1)
    aggregate_event_peak = max(before_total, after_total)
    rule_b_source_check = max(Q(1), Q(0)) + Q(1)
    assert aggregate_event_peak == 1 and rule_b_source_check == 2
    evidence = dict(scope='Fixed schedules, exact rational arithmetic; not a search or a general proof',
                    ai_example=dict(early=early, late=late, reception_boundary_peaks=reception),
                    independent_quota_counterexample=dict(earlier_prefix=p1, later_prefix=p2,
                                                           earlier_completion=bad, later_completion=good),
                    rule_b_event_semantics=dict(capacity='1',
                        release_then_admit_peak=str(aggregate_event_peak),
                        rule_b_source_check=str(rule_b_source_check),
                        conclusion='Conservative model change, not a refutation under its own Rule B'))
    destination = Path(__file__).resolve().parents[2] / 'output/safe_interval_review_20261021/fixed_checks.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes((json.dumps(evidence, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(f'Fixed schedule assertions passed; evidence: {destination}')


if __name__ == '__main__':
    main()
