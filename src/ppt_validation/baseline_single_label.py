"""單節點單Label的貪婪對照組；不是完整CGR或SABR，不保證找到可行解。"""
from dataclasses import asdict
from fractions import Fraction as F
import heapq

from src.validation.model import peak, validate_input
from .search import Label, receiver_candidates, transmission_free, contact_usage


def search(case, bundle, quota, background, calendar, max_labels=100000):
    """共用相同延伸限制，只把每個節點保留的Label限制為最早一個。"""
    validate_input(case,bundle)
    contacts={c['id']:c for c in case['contacts']}
    outgoing={v:[] for v in case['buffers']}
    for c in sorted(case['contacts'],key=lambda c:c['id']):outgoing[c['u']].append(c)
    labels={'L0':Label(None,bundle['g'],None,None)}
    best={bundle['source']:'L0'}
    queue=[(bundle['g'],0,'L0')]
    serial,expanded,discarded=0,0,0
    trace=[]

    def node(label):
        return bundle['source'] if label.c is None else contacts[label.c]['v']

    def finish(arrival,hops):
        return dict(arrival=arrival,hops=hops,
            labels={lid:asdict(lab) for lid,lab in labels.items()},trace=trace,
            labels_created=len(labels),labels_expanded=expanded,
            baseline_discarded=discarded,baseline='single_earliest_label_per_node',
            no_route_is_not_infeasibility_proof=True)

    while queue:
        _,_,lid=heapq.heappop(queue)
        lab=labels[lid];u=node(lab)
        if best[u]!=lid:
            trace.append(dict(event='STALE',label=lid))
            continue
        trace.append(dict(event='POP',label=lid,node=u,A=lab.A))
        if u==bundle['dest']:
            if lab.pred is None:
                value,_=peak(background,u,[[lab.A,lab.A,bundle['size'],bundle['size']]])
                if value>case['buffers'][u]:return finish(None,[])
            hops=[]
            while lab.pred is not None:
                hops.append((lab.c,lab.s));lab=labels[lab.pred]
            return finish(labels[lid].A,list(reversed(hops)))
        expanded+=1
        for c in outgoing[u]:
            used=contact_usage(labels,lid,c['id'],bundle['size'])
            if used+bundle['size']>quota[c['id']]:continue
            for detail in receiver_candidates(case,bundle,lab,c,background):
                event=dict(event='CANDIDATE',label=lid,contact=c['id'],**detail)
                if detail['reason']=='RECEIVER_PASS':
                    if not transmission_free(calendar,c['id'],detail['s'],detail['f']):
                        event['reason']='CONTACT_BUSY'
                    else:
                        send=[[lab.A,detail['s'],bundle['size'],bundle['size']],
                              [detail['s'],detail['f'],bundle['size'],F(0)]]
                        value,when=peak(background,u,send)
                        event.update(sender_peak=value,sender_peak_time=when)
                        if value>case['buffers'][u]:event['reason']='SENDER_BUFFER'
                        elif c['v'] in best and labels[best[c['v']]].A<=detail['A']:
                            # 本對照組的貪婪保留規則，不稱為已證明的dominance。
                            event['reason']='BASELINE_EARLIER_LABEL_KEPT';discarded+=1
                        else:
                            if len(labels)>=max_labels:
                                raise RuntimeError('INCOMPLETE_BASELINE_LABEL_LIMIT')
                            serial+=1;nid=f'L{serial}'
                            labels[nid]=Label(c['id'],detail['A'],detail['s'],lid)
                            best[c['v']]=nid
                            heapq.heappush(queue,(detail['A'],serial,nid))
                            event.update(reason='PASS',new_label=nid)
                trace.append(event)
    return finish(None,[])
