"""完整排程核對：DFS＋起送時間笛卡兒積，不使用 Label 搜尋或增量檢查。"""
from collections import Counter
from fractions import Fraction as F
from itertools import product

# 舊版獨立檢查器只檢查完整路徑的時間／容量／Buffer，與路由搜尋分開。
from src.validation.exhaustive_oracle import evaluate_schedule


def evaluate(case, bundle, quota, background, calendar, hops):
    """獨立核對既有發送預約；不共用待測端 transmission_free。"""
    basic = evaluate_schedule(case, bundle, quota, background, hops)
    if not basic['feasible']:
        return basic
    contacts = {c['id']: c for c in case['contacts']}
    for cid, s in hops:
        c = contacts[cid]
        if (s / case['delta']).denominator != 1:
            return dict(feasible=False, reason='OFF_GRID')
        finish = s + bundle['size'] / c['rate']
        for booked in calendar.get(cid, []):
            # 重疊長度嚴格大於0才衝突。
            if min(finish, booked['finish']) > max(s, booked['start']):
                return dict(feasible=False, reason='CONTACT_BUSY', contact=cid,
                            s=s, f=finish, conflicting=booked)
    return basic


def solve(case, bundle, quota, background, calendar, max_schedules=1000000):
    """僅用於已確認 DAG 的小案例，完整列出每條路徑的所有時間組合。"""
    outgoing = {v: [] for v in case['buffers']}
    for c in case['contacts']:
        outgoing[c['u']].append(c)

    def paths(node, prefix, visited):
        if node == bundle['dest']:
            yield prefix
            return
        for c in outgoing[node]:
            if c['v'] in visited:
                raise ValueError('REFERENCE_REQUIRES_DAG')
            yield from paths(c['v'], prefix + [c], visited | {c['v']})

    optimum, best, count, path_count, feasible = None, [], 0, 0, 0
    rejections = Counter()
    for edges in paths(bundle['source'], [], {bundle['source']}):
        path_count += 1
        domains = []
        for c in edges:
            begin = int(-(-c['start'] // case['delta']))
            end = int((c['end'] - bundle['size']/c['rate']) // case['delta'])
            domains.append([i * case['delta'] for i in range(begin, end+1)])
        for starts in product(*domains):
            count += 1
            if count > max_schedules:
                raise RuntimeError('INCOMPLETE_REFERENCE_LIMIT: 尚未核對完成')
            hops = [(c['id'], s) for c, s in zip(edges, starts)]
            check = evaluate(case, bundle, quota, background, calendar, hops)
            if not check['feasible']:
                rejections[check['reason']] += 1
                continue
            feasible += 1
            if optimum is None or check['arrival'] < optimum:
                optimum, best = check['arrival'], hops
    return dict(arrival=optimum, hops=best, paths_considered=path_count,
                schedules_considered=count, feasible_schedules=feasible,
                rejection_counts=dict(rejections))
