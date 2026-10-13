"""時間格點 Label Setting 驗證版本：保留所有 Label，不做 dominance。

只接受無循環拓樸，供目前 PPT／八節點人工案例核對。
這是已授權的驗證版本，不是已定案的一般支配演算法。
"""
from dataclasses import dataclass, asdict
from fractions import Fraction as F
import heapq

from src.validation.model import peak


@dataclass(frozen=True)
class Label:
    """四個論文欄位；Label 編號是外部索引，與 contact 編號無關。"""
    c: str | None
    A: F
    s: F | None
    pred: str | None


def require_dag(case):
    """明確限制本輪測試範圍，遇到循環拒絕執行，不默默刪路徑。"""
    adjacent = {v: [] for v in case['buffers']}
    indegree = {v: 0 for v in adjacent}
    for c in case['contacts']:
        adjacent[c['u']].append(c['v'])
        indegree[c['v']] += 1
    pending = [v for v in adjacent if indegree[v] == 0]
    count = 0
    while pending:
        v = pending.pop()
        count += 1
        for w in adjacent[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                pending.append(w)
    if count != len(adjacent):
        raise ValueError('UNSUPPORTED_CYCLIC_TOPOLOGY: 本輪僅驗證 DAG')


def transmission_free(calendar, cid, start, finish):
    """發送使用半開區間 [start,finish)，允許相鄰兩包首尾相接。"""
    return all(finish <= item['start'] or start >= item['finish']
               for item in calendar.get(cid, []))


def receiver_candidates(case, bundle, label, contact, background):
    """逐格產生候選及判斷資訊；某個 s 失敗，仍繼續後面的 s。"""
    duration = bundle['size'] / contact['rate']
    first = max(label.A, contact['start'])
    last = contact['end'] - duration
    # 對齊全域 Δ 格點，非整格的 first 也不可直接當起點。
    slot = int(-(-first // case['delta']))
    s = slot * case['delta']
    while s <= last:
        finish = s + duration
        h, arrival = s + contact['delay'], finish + contact['delay']
        receive = [[h, arrival, F(0), bundle['size']]]
        value, when = peak(background, contact['v'], receive)
        reason = ('DEADLINE' if arrival > case['horizon'] else
                  'RECEIVER_BUFFER' if value > case['buffers'][contact['v']]
                  else 'RECEIVER_PASS')
        yield dict(s=s, f=finish, h=h, A=arrival,
                   receiver_peak=value, receiver_peak_time=when, reason=reason)
        s += case['delta']


def search(case, bundle, quota, background, calendar, max_labels=100000):
    """以完整抵達時間 ExtractMin；只有取出目的地才結束搜尋。"""
    require_dag(case)
    contacts = {c['id']: c for c in case['contacts']}
    labels = {'L0': Label(None, bundle['g'], None, None)}
    queue = [(bundle['g'], 0, 'L0')]
    trace, serial, expanded = [], 0, 0
    outgoing = {v: [] for v in case['buffers']}
    for c in sorted(case['contacts'], key=lambda x: x['id']):
        outgoing[c['u']].append(c)

    def result(arrival, hops):
        return dict(arrival=arrival, hops=hops,
                    labels={lid: asdict(lab) for lid, lab in labels.items()},
                    trace=trace, labels_created=len(labels), labels_expanded=expanded)

    while queue:
        _, _, lid = heapq.heappop(queue)
        label = labels[lid]
        node = bundle['source'] if label.c is None else contacts[label.c]['v']
        trace.append(dict(event='POP', label=lid, node=node, A=label.A,
                          queue_size=len(queue)))
        if node == bundle['dest']:
            # 同節點本地交付僅檢查交付前瞬間，沒有額外來源准入步驟。
            if label.pred is None:
                value, _ = peak(background, node, [[label.A, label.A,
                                                    bundle['size'], bundle['size']]])
                if value > case['buffers'][node]:
                    trace.append(dict(event='LOCAL_DELIVERY_BUFFER_FAIL'))
                    return result(None, [])
            hops, current = [], label
            while current.pred is not None:
                hops.append((current.c, current.s))
                current = labels[current.pred]
            trace.append(dict(event='GOAL', label=lid, A=label.A))
            return result(label.A, list(reversed(hops)))
        expanded += 1
        for c in outgoing[node]:
            # DAG 中一條路徑不會重用同一 contact，容量直接判斷 S <= R[c]。
            if bundle['size'] > quota[c['id']]:
                trace.append(dict(event='CONTACT_REJECT', label=lid,
                                  contact=c['id'], reason='CAPACITY'))
                continue
            attempted = False
            for candidate in receiver_candidates(case, bundle, label, c, background):
                attempted = True
                event = dict(event='CANDIDATE', label=lid, contact=c['id'], **candidate)
                if candidate['reason'] == 'RECEIVER_PASS':
                    if not transmission_free(calendar, c['id'], candidate['s'], candidate['f']):
                        event['reason'] = 'CONTACT_BUSY'
                    else:
                        sender = [[label.A, candidate['s'], bundle['size'], bundle['size']],
                                  [candidate['s'], candidate['f'], bundle['size'], F(0)]]
                        value, when = peak(background, node, sender)
                        event.update(sender_peak=value, sender_peak_time=when)
                        if value > case['buffers'][node]:
                            event['reason'] = 'SENDER_BUFFER'
                        else:
                            if len(labels) >= max_labels:
                                raise RuntimeError('INCOMPLETE_LABEL_LIMIT: 不可當作無解')
                            serial += 1
                            nid = f'L{serial}'
                            labels[nid] = Label(c['id'], candidate['A'], candidate['s'], lid)
                            heapq.heappush(queue, (candidate['A'], serial, nid))
                            event.update(reason='PASS', new_label=nid, priority=[candidate['A'], serial])
                event['queue_size'] = len(queue)
                trace.append(event)
            if not attempted:
                trace.append(dict(event='CONTACT_REJECT', label=lid,
                                  contact=c['id'], reason='NO_START_IN_WINDOW'))
    trace.append(dict(event='EXHAUSTED'))
    return result(None, [])
