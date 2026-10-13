"""從已核對Ring Road取短時窗，執行固定五包傳送測試。"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import shutil

from src.experiments.config import load_scenario
from .prepare_ring_road import SOURCE_SHA256, SOURCE_URL, convert_contacts
from .run import run, write_json
from .temporal_reference import solve_temporal


def execute(source, config, local, published, draw=True):
    source,config,local,published=map(Path,(source,config,local,published))
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    spec=json.loads(config.read_text(encoding='utf-8'))
    first,last=F(spec['window_start_s']),F(spec['window_end_s'])
    if not 0<=first<last<=86400:
        raise ValueError('INVALID_PILOT_WINDOW')
    if F(spec['rate_MB_s'])!=F(1,10) or F(spec['propagation_delay_s'])!=0:
        raise ValueError('PILOT_REQUIRES_DECLARED_THESIS_RATE_AND_ZERO_DELAY')
    contacts,_=convert_contacts(source.read_text(encoding='utf-8'))
    subset=[]
    for c in contacts:
        lo,hi=max(first,F(c['start'])),min(last,F(c['end']))
        if lo<hi:
            subset.append(dict(c,start=str(lo),end=str(hi),
                               remaining_capacity=str((hi-lo)*F(c['rate']))))
    local.mkdir(parents=True,exist_ok=False)
    experiment=dict(schema_version=1,name=spec['name'],
        units=dict(time='s',data='MB',rate='MB/s'),
        time_step=spec['time_step_s'],horizon=str(last),
        nodes=[dict(id=str(i),buffer=spec['buffer_MB']) for i in range(1,48)],
        contacts=subset,bundles=spec['bundles'])
    write_json(local/'experiment.json',experiment)
    case=load_scenario(local/'experiment.json')
    manifest=dict(source_url=SOURCE_URL,source_sha256=SOURCE_SHA256,
        original_nodes=47,original_contacts=3172,retained_nodes=len(case['buffers']),
        active_window_contacts=len(subset),window_start_s=str(first),window_end_s=str(last),
        contact_times_clipped=True,quota_recomputed_for_clipped_window=True,
        short_contacts_removed=False,cycles_removed=False,dominance=False,
        scenario_parameters=spec,
        traffic_selection=spec.get('traffic_selection',
            'explicit shared 9 -> 41 -> 2 corridor; selected connectivity smoke test'),
        full_day_test=False,random_traffic=False,physical_simulation=False)
    write_json(local/'manifest.json',manifest)
    # 保留同一待測搜尋，只替換獨立完整列舉的組合產生方式。
    result=run(case,local/'run',reference_solver=solve_temporal)
    if draw:
        from .figures import generate
        shown=[]
        edges={c['id']:c for c in case['contacts']}
        for r in result['records']:
            for node in [r['bundle']['source']]+[edges[cid]['v'] for cid,_ in r['hops']]:
                if node not in shown: shown.append(node)
        generate(local/'run',nodes=shown,time_origin=first,buffer_zoom=True)
    published.mkdir(parents=True,exist_ok=False)
    for filename in ['summary.csv','schedule.csv','statistics.json','status.json','report.md']:
        shutil.copy2(local/'run'/filename,published/filename)
    if draw:
        shutil.copytree(local/'run/figures',published/'figures')
    write_json(published/'manifest.json',manifest)
    write_json(published/'verification.json',dict(
        queries=[dict(bundle=r['bundle']['id'],arrival=r['arrival'],hops=r['hops'],
            labels_created=r['labels_created'],labels_expanded=r['labels_expanded'],
            full_schedule_check=r['full_schedule_check'],independent=r['independent'])
            for r in result['records']],
        all_queries_match_reference=True,general_correctness_proven=False))
    for record in result['records']:
        print(record['bundle']['id'],record['status'],'arrival=',record['arrival'],
              'hops=',record['hops'],'labels=',record['labels_created'])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--config',required=True)
    parser.add_argument('--local',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--no-figures',action='store_true')
    args=parser.parse_args()
    execute(args.source,args.config,args.local,args.output,draw=not args.no_figures)
