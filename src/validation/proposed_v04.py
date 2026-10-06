"""Literal finite-grid v04 implementation. No calendar, no strengthened pruning."""
import heapq
from fractions import Fraction as F
from .model import peak, occupancy, validate_input


def dominates(a, b, background, capacity, size):
    if a['v'] != b['v'] or a['a'] > b['a']:
        return False
    if any(a['usage'].get(c, 0) > b['usage'].get(c, 0)
           for c in a['usage'].keys() | b['usage'].keys()):
        return False
    p, _ = peak(background, a['v'], [[a['a'], b['a'], size, size]])
    return p <= capacity[a['v']]


def check_extension(case, bundle, quota, background, label, c, s):
    S = bundle['size']
    x = S/c['rate']
    f, h, arrival = s+x, s+c['delay'], s+x+c['delay']
    if label['v'] != c['u']:
        return False, {'reason': 'NODE_CONTINUITY'}
    temporal = s >= max(label['a'], c['start']) and f <= c['end'] and arrival <= case['horizon']
    q = label['usage'].get(c['id'], F(0))+S <= quota[c['id']]
    detail = {'temporal': temporal, 'quota': q, 's': s, 'f': f, 'h': h, 'arrival': arrival}
    if not temporal or not q:
        return False, {**detail, 'reason': 'TEMPORAL' if not temporal else 'QUOTA'}
    send = [[label['a'], s, S, S], [s, f, S, F(0)]]
    receive = [[h, arrival, F(0), S]]
    ps, ts = peak(background, c['u'], send)
    pr, tr = peak(background, c['v'], receive)
    ok = ps <= case['buffers'][c['u']] and pr <= case['buffers'][c['v']]
    return ok, {**detail, 'sender_peak': ps, 'sender_peak_time': ts,
                'receiver_peak': pr, 'receiver_peak_time': tr,
                'reason': 'PASS' if ok else 'BUFFER'}


def search(case, bundle, quota, background, dominance=True):
    validate_input(case, bundle)
    labels, heap, trace = {}, [], []
    stats = {'created': 0, 'enqueued': 0, 'expanded': 0, 'pruned_new': 0, 'pruned_old': 0}
    if occupancy(background, bundle['source'], bundle['g'])+bundle['size'] > case['buffers'][bundle['source']]:
        return {'arrival': None, 'hops': [], 'labels': {}, 'trace': [{'event': 'SOURCE_FAIL'}], 'stats': stats}
    root = {'id': 'L0', 'v': bundle['source'], 'a': bundle['g'], 'usage': {},
            'pred': None, 'hop': None, 'active': True, 'processed': False}
    labels['L0'] = root
    heapq.heappush(heap, (root['a'], 0, 'L0'))
    stats['created'] = stats['enqueued'] = 1
    serial = 0
    def queue():
        return [i for _, _, i in sorted(heap)]
    while heap:
        before = queue()
        _, _, lid = heapq.heappop(heap)
        L = labels[lid]
        if not L['active']:
            trace.append({'event': 'STALE', 'queue_before': before, 'selected': lid, 'queue_after': queue()})
            continue
        if L['v'] == bundle['dest']:
            hops, K = [], L
            while K['pred'] is not None:
                hops.append(K['hop']); K = labels[K['pred']]
            trace.append({'event': 'GOAL', 'queue_before': before, 'selected': lid, 'queue_after': queue()})
            return {'arrival': L['a'], 'hops': list(reversed(hops)), 'labels': labels, 'trace': trace, 'stats': stats}
        stats['expanded'] += 1
        trace.append({'event': 'POP', 'queue_before': before, 'selected': lid, 'queue_after': queue()})
        for c in sorted(case['contacts'], key=lambda c: c['id']):
            if c['u'] != L['v']:
                continue
            start = max(L['a'], c['start'])
            last = c['end']-bundle['size']/c['rate']
            if L['usage'].get(c['id'], 0)+bundle['size'] > quota[c['id']]:
                trace.append({'event': 'CONTACT_QUOTA_FAIL', 'selected': lid, 'contact': c['id'],
                              'used': L['usage'].get(c['id'], 0), 'quota': quota[c['id']],
                              'queue_before': queue(), 'queue_after': queue()})
                continue
            if start > last:
                trace.append({'event': 'CONTACT_TIME_FAIL', 'selected': lid, 'contact': c['id'],
                              'earliest': start, 'latest': last, 'queue_before': queue(), 'queue_after': queue()})
                continue
            s = start
            while s <= last:
                qb = queue()
                ok, details = check_extension(case, bundle, quota, background, L, c, s)
                event = {'event': 'EXTEND', 'selected': lid, 'contact': c['id'],
                         'queue_before': qb, **details}
                if ok:
                    serial += 1
                    nid = f'L{serial}'
                    usage = dict(L['usage']); usage[c['id']] = usage.get(c['id'], F(0))+bundle['size']
                    N = {'id': nid, 'v': c['v'], 'a': details['arrival'], 'usage': usage,
                         'pred': lid, 'hop': (c['id'], s), 'active': True, 'processed': False}
                    stats['created'] += 1
                    existing = [K for K in labels.values() if K['active'] and K['v'] == N['v']]
                    dominators = [K['id'] for K in existing if dominance and dominates(K, N, background, case['buffers'], bundle['size'])]
                    event['new_label'] = nid
                    if dominators:
                        N['active'] = False; stats['pruned_new'] += 1
                        event['dominated_by'] = dominators
                    else:
                        removed = []
                        for K in existing:
                            if dominance and dominates(N, K, background, case['buffers'], bundle['size']):
                                K['active'] = False; removed.append(K['id']); stats['pruned_old'] += 1
                        event['removed'] = removed
                        heapq.heappush(heap, (N['a'], serial, nid)); stats['enqueued'] += 1
                    labels[nid] = N
                event['queue_after'] = queue(); trace.append(event)
                s += case['delta']
        L['processed'] = True
    trace.append({'event': 'EXHAUSTED', 'queue_before': [], 'queue_after': []})
    return {'arrival': None, 'hops': [], 'labels': labels, 'trace': trace, 'stats': stats}
