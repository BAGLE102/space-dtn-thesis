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


def solve(case, bundle, quota, background, calendar, max_schedules=1000000,
          max_walk_prefixes=1000000):
    """允許繞圈，以正的每跳耗時推導有限深度，再核對完整排程。"""
    outgoing = {v: [] for v in case['buffers']}
    for c in case['contacts']:
        outgoing[c['u']].append(c)

    # 最小每跳耗時>0，任何可行walk的hop數不超過此上界。
    hop_times = [bundle['size']/c['rate'] + c['delay'] for c in case['contacts']]
    if any(t <= 0 for t in hop_times):
        raise ValueError('REFERENCE_REQUIRES_POSITIVE_HOP_TIME')
    depth_bound = (int((case['horizon']-bundle['g']) // min(hop_times))
                   if hop_times else 0)
    prefixes = 0

    def paths():
        # 用stack取代遞迴，不以visited集合排除節點或contact重訪。
        nonlocal prefixes
        pending = [(bundle['source'], [])]
        while pending:
            node, prefix = pending.pop()
            prefixes += 1
            if prefixes > max_walk_prefixes:
                raise RuntimeError('INCOMPLETE_REFERENCE_WALK_LIMIT: 尚未核對完成')
            if node == bundle['dest']:
                yield prefix
                continue
            if len(prefix) >= depth_bound:
                continue
            for c in reversed(outgoing[node]):
                pending.append((c['v'], prefix + [c]))

    optimum, best, count, path_count, feasible = None, [], 0, 0, 0
    rejections = Counter()
    for edges in paths():
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
                rejection_counts=dict(rejections), depth_bound=depth_bound,
                walk_prefixes_considered=prefixes)
