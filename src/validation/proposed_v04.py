# 現行有限格點搜尋核心：本次只加註解；仍是 aggregate 容量，未加入鏈路時段互斥。
"""Literal finite-grid v04 implementation. No calendar, no strengthened pruning."""
import heapq
from fractions import Fraction as F
from .model import peak, occupancy, validate_input


# 同節點、較早抵達、各 Contact 用量不更多且能持包等待，才可取代另一 Label。
def dominates(a, b, background, capacity, size):
    # a、b 是兩個 Label；先確認接收節點相同且 a 不比 b 晚抵達。
    if a['v'] != b['v'] or a['a'] > b['a']:
        return False
    if any(a['usage'].get(c, 0) > b['usage'].get(c, 0)
           for c in a['usage'].keys() | b['usage'].keys()):
        return False
    # 即使早到，也必須能在這段時間持有整包，才能複製 b 的後續安排。
    p, _ = peak(background, a['v'], [[a['a'], b['a'], size, size]])
    return p <= capacity[a['v']]


# 只驗證一個 (Label, Contact, 起送時間) 的延伸，不修改既有 R 或 O。
def check_extension(case, bundle, quota, background, label, c, s):
    S = bundle['size']
    x = S/c['rate']
    # f：最後 byte 送出；h：第一個 byte 抵達；arrival：整包完整抵達。
    f, h, arrival = s+x, s+c['delay'], s+x+c['delay']
    if label['v'] != c['u']:
        return False, {'reason': 'NODE_CONTINUITY'}
    temporal = s >= max(label['a'], c['start']) and f <= c['end'] and arrival <= case['horizon']
    q = label['usage'].get(c['id'], F(0))+S <= quota[c['id']]
    detail = {'temporal': temporal, 'quota': q, 's': s, 'f': f, 'h': h, 'arrival': arrival}
    if not temporal or not q:
        return False, {**detail, 'reason': 'TEMPORAL' if not temporal else 'QUOTA'}
    # 線段格式為 [起點時間, 終點時間, 起點占用, 終點占用]。
    # 傳送端先等待再逐 byte 釋放；接收端逐 byte 填入，不先預留整包。
    send = [[label['a'], s, S, S], [s, f, S, F(0)]]
    receive = [[h, arrival, F(0), S]]
    ps, ts = peak(background, c['u'], send)
    pr, tr = peak(background, c['v'], receive)
    ok = ps <= case['buffers'][c['u']] and pr <= case['buffers'][c['v']]
    return ok, {**detail, 'sender_peak': ps, 'sender_peak_time': ts,
                'receiver_peak': pr, 'receiver_peak_time': tr,
                'reason': 'PASS' if ok else 'BUFFER'}


# 有限格點單包搜尋；保留所有必要候選，取出有效目的地 Label 後沿 pred 回溯。
def search(case, bundle, quota, background, dominance=True):
    validate_input(case, bundle)
    labels, heap, trace = {}, [], []
    stats = {'created': 0, 'enqueued': 0, 'expanded': 0, 'pruned_new': 0, 'pruned_old': 0}
    if occupancy(background, bundle['source'], bundle['g'])+bundle['size'] > case['buffers'][bundle['source']]:
        return {'arrival': None, 'hops': [], 'labels': {}, 'trace': [{'event': 'SOURCE_FAIL'}], 'stats': stats}
    # usage 是前驅鏈各 Contact 用量的內部快取；論文 Label 仍以 c/A/s/pred 表示。
    # root 沒有實際 incoming Contact，所以 hop 與 pred 都是 None。
    root = {'id': 'L0', 'v': bundle['source'], 'a': bundle['g'], 'usage': {},
            'pred': None, 'hop': None, 'active': True, 'processed': False}
    labels['L0'] = root
    # heap 的三項為抵達時間、建立序號、Label ID；同時間用序號穩定排序。
    heapq.heappush(heap, (root['a'], 0, 'L0'))
    stats['created'] = stats['enqueued'] = 1
    serial = 0
    # 匯出按 heap 順序排列的 Label ID，供 trace 重播；不是另一份路由決策。
    def queue():
        return [i for _, _, i in sorted(heap)]
    while heap:
        before = queue()
        _, _, lid = heapq.heappop(heap)
        L = labels[lid]
        # 被支配的舊項目可暫留在 heap，但不能再展開；紀錄仍供其他 Label 回溯。
        if not L['active']:
            trace.append({'event': 'STALE', 'queue_before': before, 'selected': lid, 'queue_after': queue()})
            continue
        # 以「取出有效目的地 Label」終止，不是在第一次產生目的地候選時就終止。
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
            # 容量是總資料量：若不足，這個 Contact 的所有起送時間都不可用。
            if L['usage'].get(c['id'], 0)+bundle['size'] > quota[c['id']]:
                trace.append({'event': 'CONTACT_QUOTA_FAIL', 'selected': lid, 'contact': c['id'],
                              'used': L['usage'].get(c['id'], 0), 'quota': quota[c['id']],
                              'queue_before': queue(), 'queue_after': queue()})
                continue
            if start > last:
                trace.append({'event': 'CONTACT_TIME_FAIL', 'selected': lid, 'contact': c['id'],
                              'earliest': start, 'latest': last, 'queue_before': queue(), 'queue_after': queue()})
                continue
            # 對同一個 Contact 從最早到最晚逐格枚舉，不能只試第一個 s。
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
                    # dominance 在入隊前執行；已展開但仍有效的同節點 Label 也參與。
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
                                # 只失效，不刪 labels[K.id]，否則可能切斷別人的 pred。
                                K['active'] = False; removed.append(K['id']); stats['pruned_old'] += 1
                        event['removed'] = removed
                        heapq.heappush(heap, (N['a'], serial, nid)); stats['enqueued'] += 1
                    labels[nid] = N
                event['queue_after'] = queue(); trace.append(event)
                # 此行不在 if ok 內：某個 s 失敗後，仍繼續試後面的 s。
                s += case['delta']
        # processed 只表示已展開；不是把整個實體節點永久 settled。
        L['processed'] = True
    trace.append({'event': 'EXHAUSTED', 'queue_before': [], 'queue_after': []})
    return {'arrival': None, 'hops': [], 'labels': labels, 'trace': trace, 'stats': stats}
