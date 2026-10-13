"""將已核對的公開Ring Road資料轉成學長論文參數，僅準備輸入。"""
import argparse
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = 'fe363dabdd182e292f5e3b74a28558245b2caf9d3aa7730db60d52afdb9763d2'
SOURCE_URL = ('https://api.bitbucket.org/2.0/repositories/lcd-unc-ar/dtnsim/src/'
              '56d2c9835f6706563566768de646f9442a8602ab/dtnsim/simulations/'
              'hindawi_rrn/contactPlan/'
              'RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt')


def convert_contacts(text):
    """保留原始順序與方向，移除額外Server48；不裁切時窗。"""
    contacts, removed, original_rates, ranges = [], 0, set(), []
    original_index = 0
    for line in text.splitlines():
        fields = line.split()
        if fields[:2] == ['a', 'range']:
            ranges.append(F(fields[-1]))
        if fields[:2] != ['a', 'contact']:
            continue
        original_index += 1
        if len(fields) != 7:
            raise ValueError('INVALID_SOURCE_CONTACT')
        _, _, start, end, u, v, rate = fields
        if '48' in (u, v):
            removed += 1
            continue
        start, end, rate = F(start), F(end), F(rate)
        if not (0 <= start < end <= 86400 and rate > 0):
            raise ValueError('INVALID_SOURCE_TIME_OR_RATE')
        if start.denominator != 1 or end.denominator != 1:
            raise ValueError('SOURCE_TIME_NOT_INTEGER')
        original_rates.add(str(rate))
        # 明確採十進位：100KB/s=0.1MB/s；δ=0是初步實驗假設。
        contacts.append(dict(id=f'rrn_{original_index:04d}', source=u, target=v,
                             start=str(start), end=str(end), rate='1/10', delay='0',
                             remaining_capacity=str((end-start)/10)))
    audit = dict(original_contacts=original_index, removed_server_contacts=removed,
                 original_rates_bytes_s=sorted(original_rates), range_rows=len(ranges),
                 range_values=sorted({str(x) for x in ranges}))
    return contacts, audit


def prepare(source, output):
    """核對固定SHA後另存轉換結果，不覆寫原檔、不執行路由。"""
    source, output = Path(source), Path(output)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    contacts, audit = convert_contacts(source.read_text(encoding='utf-8'))
    nodes = {n for c in contacts for n in (c['source'], c['target'])}
    if nodes != {str(i) for i in range(1,48)} or len(contacts) != 3172:
        raise ValueError('THESIS_SCALE_MISMATCH')
    if audit['removed_server_contacts'] != 12:
        raise ValueError('SERVER_REMOVAL_MISMATCH')
    output.mkdir(parents=True, exist_ok=False)
    with (output/'contacts.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(contacts[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(contacts)
    topology = dict(units=dict(time='s',data='MB',rate='MB/s'),
                    nodes=[dict(id=str(i),buffer='30') for i in range(1,48)],
                    contacts_file='contacts.csv')
    audit.update(source_url=SOURCE_URL,source_sha256=digest,
                 scenario='public Walker Ring Road with thesis-reported parameters',
                 exact_senior_input_verified=False,converted_contacts=len(contacts),
                 nodes=47,horizon_s=86400,rate_MB_s='1/10',buffer_MB='30',
                 units_convention='decimal KB=1000B, MB=1000000B',
                 rate_change='12500 Bytes/s source -> 100000 Bytes/s thesis setting',
                 propagation_delay_s=0,propagation_delay_is_assumption=True,
                 contact_windows_clipped=False,short_contacts_removed=False,
                 bundle_demands_selected=False,routing_experiment_run=False,
                 current_ppt_engine_support='Cyclic walks supported and small-case validated; full-day run not performed')
    for name,data in [('topology.json',topology),('source_and_parameters.json',audit)]:
        (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',
                                encoding='utf-8',newline='\n')
    print(f'Prepared {len(nodes)} nodes / {len(contacts)} contacts in {output}')
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    prepare(args.source,args.output)
