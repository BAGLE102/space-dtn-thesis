"""Structural correctness comparison, not a CPU/memory performance benchmark."""
from pathlib import Path
import json
import csv
from .validation_cases import cases
from .proposed_v04 import search
from .model import commit, jsonable
from .exhaustive_oracle import evaluate_schedule

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'validation'


def run():
    gate=json.loads((OUT/'comparison_gate.json').read_text(encoding='utf-8'))
    if gate['status']!='PASS_FINITE_CASES':
        raise RuntimeError('STOP: oracle gate is not clear; do not compare pruning')
    records=[]
    for case in cases():
        q={c['id']:c['quota'] for c in case['contacts']};o=case['background']
        for b in case['bundles']:
            off=search(case,b,q,o,False);on=search(case,b,q,o,True)
            same=off['arrival']==on['arrival']
            valid=all(r['arrival'] is None or evaluate_schedule(case,b,q,o,r['hops'])['feasible'] for r in (off,on))
            row=dict(case=case['name'],bundle=b['id'],off=off,on=on,same_optimal_value=same,
                     both_routes_valid=valid,same_route=off['hops']==on['hops'])
            if not same or not valid:
                (OUT/'counterexample_dominance.json').write_text(json.dumps(jsonable(row),indent=2),encoding='utf-8')
                (OUT/'comparison_gate.json').write_text(json.dumps(dict(status='STOP',reason='dominance mismatch')),encoding='utf-8')
                raise AssertionError('STOP: dominance mismatch preserved; no algorithm repair')
            records.append(row)
            if on['arrival'] is not None:q,o=commit(case,q,o,b,on['hops'])
    (OUT/'dominance_results.json').write_text(json.dumps(jsonable(records),ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'dominance_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['Case','Bundle','Arrival OFF','Arrival ON','Enqueued OFF','Enqueued ON','Created OFF','Created ON','Expanded OFF','Expanded ON','Pruned ON','Same optimal value','Same route'])
        for row in records:
            a,b=row['off'],row['on']; sa,sb=a['stats'],b['stats']
            w.writerow([row['case'],row['bundle'],a['arrival'],b['arrival'],sa['enqueued'],sb['enqueued'],sa['created'],sb['created'],sa['expanded'],sb['expanded'],sb['pruned_new']+sb['pruned_old'],row['same_optimal_value'],row['same_route']])
    print([(r['case'],r['bundle'],r['off']['stats']['enqueued'],r['on']['stats']['enqueued']) for r in records])

if __name__=='__main__':run()
