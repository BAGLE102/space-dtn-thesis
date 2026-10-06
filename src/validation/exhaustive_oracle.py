"""Independent exhaustive route/schedule oracle.

Imports ONLY Python standard library. No proposed search, dominance, extension,
pruning, occupancy checker, or commit routine is imported or called.
Every topological walk up to the positive-time bound is considered; every
Cartesian product of contact start slots is checked as a COMPLETE schedule.
"""
from fractions import Fraction
from itertools import product
from collections import Counter
from copy import deepcopy

F = Fraction


def background_at(background, node, t):
    value = F(0)
    for profile in background.get(node, []):
        alternatives = []
        for left, right, yleft, yright in profile:
            if left <= t <= right:
                alternatives.append(yleft if left == right else
                                    (yleft*(right-t)+yright*(t-left))/(right-left))
        value += max(alternatives, default=F(0))
    return value


def visits_for(case, bundle, hops):
    edges = {edge['id']: edge for edge in case['contacts']}
    visits = []
    size = bundle['size']
    if not hops:
        return [dict(node=bundle['source'], kind='local', ready=bundle['g'])]
    visits.append(dict(node=bundle['source'], kind='source', ready=bundle['g'],
                       send=hops[0][1], finish=hops[0][1]+size/edges[hops[0][0]]['rate']))
    for index, (cid, start) in enumerate(hops):
        edge = edges[cid]
        first = start+edge['delay']
        full = first+size/edge['rate']
        visit = dict(node=edge['v'], first=first, ready=full)
        if index+1 == len(hops):
            visit['kind'] = 'destination'
        else:
            next_id, next_start = hops[index+1]
            visit.update(kind='transit', send=next_start,
                         finish=next_start+size/edges[next_id]['rate'])
        visits.append(visit)
    return visits


def inventory(visit, t, size):
    """Direct per-visit inventory, independent of proposed piecewise-curve code."""
    kind = visit['kind']
    if kind == 'local':
        return size if t == visit['ready'] else F(0)
    if kind == 'source':
        if t < visit['ready'] or t > visit['finish']: return F(0)
    else:
        if t < visit['first']: return F(0)
        if t < visit['ready']:
            return size*(t-visit['first'])/(visit['ready']-visit['first'])
        if kind == 'destination':
            return size if t == visit['ready'] else F(0)
        if t > visit['finish']: return F(0)
    if t <= visit['send']: return size
    return size*(visit['finish']-t)/(visit['finish']-visit['send'])


def evaluate_schedule(case, bundle, quota, background, hops):
    """No incremental resource pruning: validate a whole candidate schedule."""
    contacts = {edge['id']: edge for edge in case['contacts']}
    node, ready = bundle['source'], bundle['g']
    used = Counter()
    if not hops and node != bundle['dest']:
        return dict(feasible=False, reason='NOT_AT_DESTINATION')
    for cid, start in hops:
        edge = contacts[cid]
        if edge['u'] != node:
            return dict(feasible=False, reason='CONTINUITY')
        duration = bundle['size']/edge['rate']
        if start < ready or start < edge['start'] or start+duration > edge['end']:
            return dict(feasible=False, reason='TIMING')
        ready = start+duration+edge['delay']
        node = edge['v']
        used[cid] += bundle['size']
    if node != bundle['dest'] or ready > case['horizon']:
        return dict(feasible=False, reason='DESTINATION_OR_HORIZON')
    if any(amount > quota[cid] for cid, amount in used.items()):
        return dict(feasible=False, reason='QUOTA')
    visits = visits_for(case,bundle,hops)
    points = {bundle['g'], ready}
    for visit in visits:
        points.update(value for key,value in visit.items() if key not in ('node','kind'))
    for profiles in background.values():
        points.update(value for profile in profiles for seg in profile for value in seg[:2])
    peaks = {}
    for v in case['buffers']:
        for t in sorted(points):
            own = sum((inventory(visit,t,bundle['size']) for visit in visits if visit['node']==v), F(0))
            total = background_at(background,v,t)+own
            if v not in peaks or total > peaks[v]['value']:
                peaks[v] = dict(value=total,time=t)
            if total > case['buffers'][v]:
                return dict(feasible=False, reason='BUFFER',node=v,time=t,value=total,limit=case['buffers'][v])
    return dict(feasible=True, arrival=ready, usage=dict(used), peaks=peaks)


def solve(case, bundle, quota, background):
    outgoing = {v: [] for v in case['buffers']}
    for edge in case['contacts']:
        outgoing[edge['u']].append(edge)
    if case['contacts']:
        minimum_hop_time = min(bundle['size']/e['rate']+e['delay'] for e in case['contacts'])
        depth_bound = int((case['horizon']-bundle['g'])//minimum_hop_time)
    else:
        depth_bound = 0
    paths = []
    def walk(node, path):
        if node == bundle['dest']:
            paths.append(tuple(path)); return
        if len(path) == depth_bound: return
        for edge in outgoing[node]:
            walk(edge['v'],path+[edge['id']])
    walk(bundle['source'],[])
    edges = {e['id']:e for e in case['contacts']}
    best, optimum, feasible, schedule_count = None, None, [], 0
    rejection_counts = Counter()
    witness = {}
    for path in paths:
        domains = []
        for cid in path:
            edge = edges[cid]
            begin = -(-edge['start']//case['delta'])
            stop = (edge['end']-bundle['size']/edge['rate'])//case['delta']
            domains.append([i*case['delta'] for i in range(int(begin),int(stop)+1)])
        for starts in product(*domains):
            schedule_count += 1
            hops = list(zip(path,starts))
            result = evaluate_schedule(case,bundle,quota,background,hops)
            if not result['feasible']:
                rejection_counts[result['reason']] += 1
                witness.setdefault(result['reason'],dict(hops=hops,check=result))
                continue
            feasible.append(dict(hops=hops,arrival=result['arrival']))
            if optimum is None or result['arrival'] < optimum:
                optimum, best = result['arrival'], hops
    return dict(arrival=optimum,hops=best or [],feasible_schedules=feasible,
                paths_considered=len(paths),schedules_considered=schedule_count,
                rejection_counts=dict(rejection_counts),rejection_witnesses=witness,
                depth_bound=depth_bound)


def commit_independently(case, bundle, quota, background, hops):
    """Construct accepted visit profiles without proposed route_curves/commit."""
    q,o = deepcopy(quota),deepcopy(background)
    for cid,_ in hops: q[cid] -= bundle['size']
    for visit in visits_for(case,bundle,hops):
        size=bundle['size']; kind=visit['kind']; parts=[]
        if kind == 'local':
            parts=[[visit['ready'],visit['ready'],size,size]]
        else:
            if kind != 'source': parts.append([visit['first'],visit['ready'],F(0),size])
            if kind != 'destination':
                parts.extend([[visit['ready'],visit['send'],size,size],
                              [visit['send'],visit['finish'],size,F(0)]])
        o.setdefault(visit['node'],[]).append(parts)
    return q,o
