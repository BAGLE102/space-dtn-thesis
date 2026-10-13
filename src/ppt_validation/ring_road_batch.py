"""有上限的Ring Road批次驗證；不更動待測搜尋，保留未完成與反例。"""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

from .run import write_json, write_csv


def build_specs():
    """事先列出全部設定，不依結果挑成功案例或調整演算法。"""
    specs=[]
    def add(name,family,n,size='1/10',buffer='30',start=1342,length=10,source='9',dest='2',mixed=False):
        bundles=[dict(id=f'bundle{i}',source=('7' if mixed and i%2==0 else source),
                      destination=dest,release=str(start),size=size) for i in range(1,n+1)]
        specs.append(dict(name=name,family=family,window_start_s=str(start),
            window_end_s=str(start+length),time_step_s='1',buffer_MB=buffer,
            rate_MB_s='1/10',propagation_delay_s='0',bundles=bundles,
            traffic_selection=('alternating 9->2 and 7->2, same release; diagnostic only'
                               if mixed else f'explicit shared {source}->{dest} corridor; diagnostic only')))
    for n in [10,20,50,100]:add(f'load_{n}','bundle_count',n)
    for size,kb in [('1/5',200),('1/2',500),('1',1000)]:
        add(f'size_{kb}KB','bundle_size',20,size=size)
    for source,dest,start in [('20','5',2882),('29','1',3339),('25','3',4942),('19','3',6336)]:
        add(f'corridor_{source}_{dest}','other_corridors',10,start=start,source=source,dest=dest)
    add('mixed_sources_20','mixed_sources',20,mixed=True)
    add('buffer_200KB','buffer_sensitivity',20,buffer='1/5')
    add('window_20s','longer_window',10,length=20)
    return specs


def summarize(local,spec,returncode):
    folder=local/'run'
    status=json.loads((folder/'status.json').read_text(encoding='utf-8')) if (folder/'status.json').exists() else {}
    records=[]
    unreadable=[]
    for p in sorted(folder.glob('query_*.json')):
        try:
            records.append(json.loads(p.read_text(encoding='utf-8')))
        except (json.JSONDecodeError,UnicodeError):
            unreadable.append(p.name)
    complete=status.get('status')=='VALIDATED_SMALL_CASE'
    correct_stop=status.get('status')=='STOP'
    if correct_stop: state='STOP_CORRECTNESS'
    elif returncode==124: state='INCOMPLETE_TIMEOUT'
    elif complete and returncode==0: state='COMPLETE'
    elif 'INCOMPLETE_' in status.get('error',''): state='INCOMPLETE_SEARCH_OR_REFERENCE_LIMIT'
    else: state='ERROR'
    accepted=sum(r['arrival'] is not None for r in records)
    return dict(case=spec['name'],family=spec['family'],requested=len(spec['bundles']),
                completed_queries=len(records),accepted=accepted,
                no_route=sum(r['arrival'] is None for r in records),
                unprocessed=len(spec['bundles'])-len(records),status=state,
                window_s=int(spec['window_end_s'])-int(spec['window_start_s']),
                size_MB=spec['bundles'][0]['size'],buffer_MB=spec['buffer_MB'],
                source_pattern=spec['traffic_selection'],
                unreadable_partial_files=','.join(unreadable),
                error=status.get('error',status.get('reason','')))


def export_partial(local,output,spec):
    """只匯出完整寫入且已核對的查詢；截斷紀錄留在本機，不算完成。"""
    records=[]
    for path in sorted((local/'run').glob('query_*.json')):
        try:
            r=json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError,UnicodeError):
            continue
        if r['arrival']!=r['independent']['arrival']:
            raise RuntimeError('PARTIAL_REFERENCE_MISMATCH')
        records.append(dict(bundle=r['bundle'],status=r['status'],arrival=r['arrival'],
            hops=r['hops'],independent=r['independent'],
            full_schedule_check=r['full_schedule_check'],
            labels_created=r['labels_created'],labels_expanded=r['labels_expanded']))
    write_json(output/'partial_verified_queries.json',dict(
        requested=len(spec['bundles']),checked=len(records),records=records,
        whole_case_completed=False,unprocessed_are_not_no_route=True))


def execute(source,configs,local,output,seconds=20):
    configs,local,output=map(Path,(configs,local,output))
    for folder in [configs,local,output]:folder.mkdir(parents=True,exist_ok=False)
    specs=build_specs()
    write_json(configs/'manifest.json',dict(cases=specs,per_case_seconds=seconds,
        dominance=False,algorithm_changed=False,performance_comparison=False,
        complete_queries_checked_against_exhaustive=True))
    rows=[]
    for spec in specs:
        config=configs/f'{spec["name"]}.json';write_json(config,spec)
        destination=output/spec['name']; workspace=local/spec['name']
        cmd=[sys.executable,'-m','src.ppt_validation.ring_road_pilot',
             '--source',str(source),'--config',str(config),
             '--local',str(workspace),'--output',str(destination),'--no-figures']
        print(f'START {spec["name"]}: {len(spec["bundles"])} bundles',flush=True)
        with (local/f'{spec["name"]}.log').open('w',encoding='utf-8') as log:
            try:
                child=subprocess.run(cmd,stdout=log,stderr=log,timeout=seconds,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                code=child.returncode
            except subprocess.TimeoutExpired:code=124
        row=summarize(workspace,spec,code);rows.append(row)
        write_json(output/'batch_results.json',rows)
        write_csv(output/'batch_summary.csv',list(row),rows)
        print(f'END {row["case"]}: {row["status"]}, checked={row["completed_queries"]}, '
              f'accepted={row["accepted"]}, no_route={row["no_route"]}',flush=True)
        if row['status']!='COMPLETE':
            destination.mkdir(parents=True,exist_ok=True)
            write_json(destination/'partial_status.json',row)
            if (workspace/'run/status.json').exists():
                write_json(destination/'worker_status.json',json.loads((workspace/'run/status.json').read_text(encoding='utf-8')))
            export_partial(workspace,destination,spec)
            if row['status']=='STOP_CORRECTNESS':
                from shutil import copy2
                copy2(workspace/'run/failure.json',destination/'failure.json')
                break
    counts=Counter(r['status'] for r in rows)
    write_json(output/'batch_status.json',dict(case_states=dict(counts),planned=len(specs),
        attempted=len(rows),checked_queries=sum(r['completed_queries'] for r in rows),
        status='STOP' if 'STOP_CORRECTNESS' in counts else 'BATCH_FINISHED_WITH_EXPLICIT_STATES',
        performance_comparison_run=False))
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--configs',required=True)
    parser.add_argument('--local',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--seconds',type=int,default=20)
    args=parser.parse_args()
    execute(args.source,args.configs,args.local,args.output,args.seconds)
