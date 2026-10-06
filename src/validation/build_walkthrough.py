"""Freeze original documents and produce the trace BEFORE oracle comparisons."""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import json
from .validation_cases import walkthrough
from .proposed_v04 import search
from .model import commit, jsonable

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'output'/'validation'
DOC = ROOT/'docs'


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x).replace('\n','<br>') for x in row)+' |' for row in rows])


def label_name(labels, lid):
    k = labels[lid]
    used = ','.join(f'{c}:{x}' for c,x in k['usage'].items()) or '0'
    return f"{lid}=({k['v']},{k['a']},{{{used}}})"


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest=OUT/'frozen_document_hashes.json'
    if not manifest.exists():
        original = {p.name: sha256(p.read_bytes()).hexdigest() for p in DOC.glob('*.md')}
        manifest.write_text(json.dumps(original,indent=2),encoding='utf-8')
        (OUT/'frozen_sequential_label_setting_v04.md').write_bytes((DOC/'sequential_label_setting_v04.md').read_bytes())
    else:
        original=json.loads(manifest.read_text(encoding='utf-8'))
        assert all(sha256((DOC/name).read_bytes()).hexdigest()==digest for name,digest in original.items())
    case = walkthrough()
    quota = {c['id']: c['quota'] for c in case['contacts']}
    background = case['background']
    content = ['# Algorithm walkthrough v01', '',
               '本次驗證固定 v04，不修改規則。所有數字來自 `output/validation/walkthrough_trace.json`；來源程式 `src/validation/build_walkthrough.py`。',
               'Δ=1 秒、T=12 秒；MB、MB/s。先前五-contact 例子擴為本次固定五節點八-contact 例子，並非改演算法。',
               '## Nodes', 'X、A、B、C、D。', '## Contacts',
               table(['Contact','From','To','Start','End','Rate','Propagation','Quota'],
                     [[c[k] for k in ('id','u','v','start','end','rate','delay','quota')] for c in case['contacts']]),
               '## Node Buffer', table(['Node','Buffer Capacity'], sorted(case['buffers'].items())),
               '## Bundles', table(['Bundle','Source','Destination','Generation Time','Size'],
                    [[b[k] for k in ('id','source','dest','g','size')] for b in case['bundles']]),
               'c4 有兩個 start choices，會產生相同 contact 用量但不同 arrival 的 labels；c7 展示 quota failure、c8 展示 temporal failure。c2/c5 的 propagation=1，使發送完成與完整到達可區分。',
               '## Trace 規則', '依 contact ID 與 start time 遞增展開；heap key=(arrival,creation ID)。POP 是取出 label；EXTEND 的 Queue Before 是該次嘗試前的剩餘佇列。SKIP 表示短路後未執行，不偽稱 PASS。先檢 quota 再列舉時間，遵照 v04 pseudocode。每個嘗試各有一列與解釋。']
    records = []
    headers = ['Step','Queue Before','Selected Label','Candidate Contact','Temporal','Quota','Buffer','New Label','Dominance','Result']
    for bundle in case['bundles']:
        before_q, before_o = quota, background
        result = search(case,bundle,quota,background,True)
        content += [f"## {bundle['id']} 完整逐步執行", '初始化：'+label_name(result['labels'],'L0')]
        labels = result['labels']
        for i, e in enumerate(result['trace']):
            temporal=capacity=buf=new=dom='—'
            event = e['event']
            if event == 'POP':
                action='取出並展開'; explain='此 label 的 arrival 在佇列最早；節點本身不被永久 settled。'
            elif event == 'GOAL':
                action='回傳目的地路徑'; explain='有效 destination label 被取出才終止，不在首次產生時終止。'
            elif event == 'CONTACT_QUOTA_FAIL':
                capacity=f"FAIL: {e['used']}+{bundle['size']}>{e['quota']}"
                temporal=buf='SKIP'; action='不產生 label'; explain='前綴用量加整包大小超過 snapshot quota。'
            elif event == 'CONTACT_TIME_FAIL':
                capacity='PASS'; temporal=f"FAIL: earliest={e['earliest']}>latest={e['latest']}"
                buf='SKIP'; action='沒有候選 start'; explain='即使 quota 足夠，也無法在 contact 結束前傳完。'
            elif event == 'EXTEND':
                edge=next(c for c in case['contacts'] if c['id']==e['contact'])
                current=labels[e['selected']]
                temporal=f"{'PASS' if e['temporal'] else 'FAIL'}: s={e['s']}≥max({current['a']},{edge['start']}); f={e['f']}≤{edge['end']}; h={e['h']}, a′={e['arrival']}≤12"
                capacity=('PASS' if e['quota'] else 'FAIL')+f": {current['usage'].get(edge['id'],0)}+{bundle['size']}≤{before_q[edge['id']]}"
                if 'sender_peak' in e:
                    buf=f"{'PASS' if e['reason']=='PASS' else 'FAIL'}: sender峰值={e['sender_peak']}@{e['sender_peak_time']}; receiver峰值={e['receiver_peak']}@{e['receiver_peak_time']}；兩端上限均4"
                else:
                    buf='SKIP'
                if 'new_label' in e:
                    new=label_name(labels,e['new_label'])
                    if e.get('dominated_by'):
                        dom='被 '+','.join(e['dominated_by'])+' 取代'; action='不入列'
                        explain='同節點的保留 label 不晚到、可等待且 U 不更多。'
                    else:
                        dom='刪除 '+','.join(e['removed']) if e.get('removed') else '無 label 可取代；保留'
                        action='加入 Q'; explain='全部 extension checks 通過；提交全域預約尚未發生。'
                else:
                    action='拒絕'; explain='失敗類別 '+e['reason']+'；不建立 label。'
            elif event == 'STALE':
                action='跳過已失效 label'; explain='前驅物件仍保留以供重建。'
            else:
                action=event; explain='佇列耗盡，在本格點上無解。'
            qafter=', '.join(e.get('queue_after',[])) or '∅'
            row=[i, ', '.join(e.get('queue_before',[])) or '∅', e.get('selected','—'),e.get('contact','—'),temporal,capacity,buf,new,dom,action+'；Q after=['+qafter+']']
            content += [table(headers,[row]),f'Step {i}：{explain}', '']
        content += ['### 全部 label 定義',table(['ID','State','Active','Processed'],
                    [[lid,label_name(labels,lid),L['active'],L['processed']] for lid,L in labels.items()]),
                    '### Selected Route', ' → '.join(cid for cid,_ in result['hops']),
                    '### Arrival Time', str(result['arrival'])+' 秒', '### Contact Usage',
                    table(['Contact','Start','Finish','Complete arrival'],
                          [[cid,s,s+bundle['size']/next(c['rate'] for c in case['contacts'] if c['id']==cid),
                            s+bundle['size']/next(c['rate'] for c in case['contacts'] if c['id']==cid)+next(c['delay'] for c in case['contacts'] if c['id']==cid)] for cid,s in result['hops']])]
        quota, background = commit(case,quota,background,bundle,result['hops'])
        content += ['### Quota Update',table(['Contact','Before','Used','After'],
                    [[cid,before_q[cid],before_q[cid]-quota[cid],quota[cid]] for cid in quota]),
                    '### Buffer Reservation / Occupancy',
                    table(['Node','Time Interval','Bundle','Occupied Buffer'],
                          [[v,f'[{lo},{hi}]',bundle['id'], f'{y0} → {y1} MB（線性）']
                           for v, curves in background.items()
                           for curve in curves[len(before_o.get(v,[])):]
                           for lo,hi,y0,y1 in curve]),
                    '同一條曲線相鄰段的共用端點只計一次。Source 從 generation 占 S；destination 在完整交付前檢查峰值、交付後釋放。']
        records.append(dict(bundle=bundle,quota_before=before_q,background_before=before_o,result=result,quota_after=quota,background_after=background))
    content += ['## 驗證狀態','本文件先由 frozen proposed implementation 產生。是否與 independent oracle 一致，另見 oracle_validation_v01.md；本 trace 本身不是獨立正確性證據。']
    (DOC/'algorithm_walkthrough_v01.md').write_text('\n\n'.join(content),encoding='utf-8')
    (OUT/'walkthrough_trace.json').write_text(json.dumps(jsonable({'case':case,'runs':records}),ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'walkthrough_input.json').write_text(json.dumps(jsonable(case),ensure_ascii=False,indent=2),encoding='utf-8')
    print([(r['bundle']['id'],str(r['result']['arrival']),r['result']['hops'],r['result']['stats']) for r in records])

if __name__ == '__main__': run()
