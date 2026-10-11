"""Execution adapter for frozen v04; same candidates, checks, dominance and ties.

Index outgoing contacts/active labels and omit per-event queue copies. The frozen
implementation stays untouched. Pruned labels cannot have descendants before
enqueueing, so only active/previously-enqueued labels need reconstruction records.
Statistics count EVERY feasible candidate, including discarded candidates.
"""
import heapq
from collections import Counter
from fractions import Fraction as F

from src.validation.model import occupancy, validate_input
from src.validation.proposed_v04 import check_extension, dominates


def search(case, bundle, quota, background, dominance=True, trace_events=True):
    validate_input(case, bundle)
    labels, heap, trace = {}, [], []
    stats = dict(created=0, enqueued=0, expanded=0, pruned_new=0, pruned_old=0)
    events, reasons, maximum_queue = Counter(), Counter(), 0

    def record(event):
        nonlocal maximum_queue
        events[event['event']] += 1
        if event['event'] == 'EXTEND':
            reasons[event['reason']] += 1
        maximum_queue = max(maximum_queue, event.get('queue_count', 0))
        if trace_events:
            trace.append(event)

    def finish(arrival, hops):
        return dict(arrival=arrival, hops=hops, labels=labels, trace=trace, stats=stats,
                    diagnostics=dict(events=dict(events), reasons=dict(reasons),
                                     max_queue_records=maximum_queue))
    if occupancy(background, bundle['source'], bundle['g'])+bundle['size'] > case['buffers'][bundle['source']]:
        return dict(arrival=None, hops=[], labels={}, trace=[{'event':'SOURCE_FAIL'}], stats=stats)
    root = dict(id='L0', v=bundle['source'], a=bundle['g'], usage={}, pred=None,
                hop=None, active=True, processed=False)
    labels['L0'] = root
    heapq.heappush(heap, (root['a'], 0, 'L0'))
    active = {node: {} for node in case['buffers']}
    active[root['v']]['L0'] = root
    outgoing = {node: [] for node in case['buffers']}
    for edge in sorted(case['contacts'], key=lambda edge: edge['id']):
        outgoing[edge['u']].append(edge)
    stats['created'] = stats['enqueued'] = 1
    serial = 0
    while heap:
        _, _, lid = heapq.heappop(heap)
        label = labels[lid]
        if not label['active']:
            record(dict(event='STALE', selected=lid, queue_count=len(heap)))
            continue
        if label['v'] == bundle['dest']:
            hops, previous = [], label
            while previous['pred'] is not None:
                hops.append(previous['hop'])
                previous = labels[previous['pred']]
            record(dict(event='GOAL', selected=lid, queue_count=len(heap)))
            return finish(label['a'], list(reversed(hops)))
        stats['expanded'] += 1
        record(dict(event='POP', selected=lid, queue_count=len(heap)))
        for edge in outgoing[label['v']]:
            start = max(label['a'], edge['start'])
            last = edge['end']-bundle['size']/edge['rate']
            if label['usage'].get(edge['id'], 0)+bundle['size'] > quota[edge['id']]:
                record(dict(event='CONTACT_QUOTA_FAIL', selected=lid,
                                  contact=edge['id'], queue_count=len(heap)))
                continue
            if start > last:
                record(dict(event='CONTACT_TIME_FAIL', selected=lid,
                                  contact=edge['id'], queue_count=len(heap)))
                continue
            s = start
            while s <= last:
                ok, details = check_extension(case, bundle, quota, background, label, edge, s)
                event = dict(event='EXTEND', selected=lid, contact=edge['id'], **details)
                if ok:
                    serial += 1
                    nid = f'L{serial}'
                    usage = dict(label['usage'])
                    usage[edge['id']] = usage.get(edge['id'], F(0))+bundle['size']
                    candidate = dict(id=nid, v=edge['v'], a=details['arrival'], usage=usage,
                                     pred=lid, hop=(edge['id'], s), active=True, processed=False)
                    stats['created'] += 1
                    existing = list(active[candidate['v']].values())
                    dominators = [old['id'] for old in existing if dominance and
                        dominates(old, candidate, background, case['buffers'], bundle['size'])]
                    event['new_label'] = nid
                    if dominators:
                        stats['pruned_new'] += 1
                        event['dominated_by'] = dominators
                        # This candidate never entered Q, so it cannot be a predecessor.
                    else:
                        removed = []
                        for old in existing:
                            if dominance and dominates(candidate, old, background,
                                                       case['buffers'], bundle['size']):
                                old['active'] = False
                                removed.append(old['id'])
                                del active[candidate['v']][old['id']]
                                stats['pruned_old'] += 1
                        event['removed'] = removed
                        labels[nid] = candidate
                        active[candidate['v']][nid] = candidate
                        heapq.heappush(heap, (candidate['a'], serial, nid))
                        stats['enqueued'] += 1
                event['queue_count'] = len(heap)
                record(event)
                s += case['delta']
        label['processed'] = True
    record(dict(event='EXHAUSTED', queue_count=0))
    return finish(None, [])
