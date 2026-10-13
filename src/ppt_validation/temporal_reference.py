"""獨立完整列舉：只省略時間上不可能銜接的組合，不做資源增量剪枝。"""
from collections import Counter
from fractions import Fraction as F

from .reference import evaluate


def solve_temporal(case, bundle, quota, background, calendar, max_prefixes=100000):
    """列舉所有時間可銜接walk；到目的地才核對完整資源排程。"""
    outgoing={v:[] for v in case['buffers']}
    for c in case['contacts']:
        if c['rate']<=0 or c['delay']<0:
            raise ValueError('INVALID_REFERENCE_TIME')
        outgoing[c['u']].append(c)
    if bundle['size']<=0 or case['delta']<=0:
        raise ValueError('INVALID_REFERENCE_GRID_OR_SIZE')
    pending=[(bundle['source'],bundle['g'],[])]
    best,arrival=[],None
    prefixes,schedules,feasible=0,0,0
    rejections=Counter()
    while pending:
        node,ready,hops=pending.pop()
        prefixes+=1
        if prefixes>max_prefixes:
            raise RuntimeError('INCOMPLETE_TEMPORAL_REFERENCE_LIMIT')
        if node==bundle['dest']:
            schedules+=1
            check=evaluate(case,bundle,quota,background,calendar,hops)
            if not check['feasible']:
                rejections[check['reason']]+=1
                continue
            feasible+=1
            if arrival is None or check['arrival']<arrival:
                arrival,best=check['arrival'],hops
            continue
        for c in outgoing[node]:
            duration=bundle['size']/c['rate']
            first=int(-(-max(ready,c['start'])//case['delta']))
            last=int(min(c['end']-duration,
                         case['horizon']-duration-c['delay'])//case['delta'])
            for slot in range(first,last+1):
                s=slot*case['delta']
                # 沒有visited、dominance或Buffer／quota／calendar的前綴剪枝。
                pending.append((c['v'],s+duration+c['delay'],hops+[(c['id'],s)]))
    return dict(arrival=arrival,hops=best,paths_considered=None,
                schedules_considered=schedules,feasible_schedules=feasible,
                walk_prefixes_considered=prefixes,rejection_counts=dict(rejections),
                method='complete enumeration of temporally feasible walks')
