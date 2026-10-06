"""Stop and preserve inputs on any same-model correctness discrepancy."""
from pathlib import Path
import json
import csv
from .validation_cases import cases, fractional_gap
from .proposed_v04 import search
from .model import commit, jsonable, occupancy
from .exhaustive_oracle import solve, evaluate_schedule, commit_independently, background_at

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'validation'


def write(name,data):
    (OUT/name).write_text(json.dumps(jsonable(data),ensure_ascii=False,indent=2),encoding='utf-8')


def compare_one(case):
    q={c['id']:c['quota'] for c in case['contacts']}; o=case['background']
    oq=dict(q); oo=case['background']; rows=[]
    for index,b in enumerate(case['bundles']):
        p=search(case,b,q,o,True)
        ref=solve(case,b,oq,oo)
        check=None if p['arrival'] is None else evaluate_schedule(case,b,oq,oo,p['hops'])
        expected=case['expected'][index] if case.get('expected') is not None else ref['arrival']
        match=p['arrival']==ref['arrival']==expected and (check is None or check['feasible'])
        record=dict(case=case['name'],bundle=b['id'],input=case,quota=q,background=o,
                    proposed=p,oracle=ref,route_check=check,expected=expected,match=match)
        if not match:
            write('counterexample_same_model.json',record)
            write('comparison_gate.json',dict(status='STOP',reason='same-model mismatch',case=case['name']))
            raise AssertionError('STOP: preserved counterexample; algorithm must not be changed without approval')
        if p['arrival'] is not None:
            nq,no=commit(case,q,o,b,p['hops'])
            nqo,noo=commit_independently(case,b,oq,oo,p['hops'])
            points={x for bg in (no,noo) for profiles in bg.values() for curve in profiles for seg in curve for x in seg[:2]}
            equal=nq==nqo and all(occupancy(no,v,t)==background_at(noo,v,t) for v in case['buffers'] for t in points)
            record['independent_commit_match']=equal
            if not equal:
                write('counterexample_commit.json',record)
                write('comparison_gate.json',dict(status='STOP',reason='commit mismatch'))
                raise AssertionError('STOP: sequential reservation mismatch')
            # Canonical chosen schedule keeps subsequent problems identical when ties exist.
            q,o,oq,oo=nq,no,nqo,noo
        rows.append(record)
    return rows


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for case in cases():
        records.extend(compare_one(case))
    write('oracle_results.json',records)
    with (OUT/'oracle_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['Case','Bundle','Proposed Feasible','Oracle Feasible','Proposed Arrival','Oracle Arrival','Match','Oracle paths','Oracle schedules'])
        for r in records:
            p,o=r['proposed'],r['oracle']
            w.writerow([r['case'],r['bundle'],p['arrival'] is not None,o['arrival'] is not None,
                        p['arrival'],o['arrival'],r['match'],o['paths_considered'],o['schedules_considered']])
    gap=[]
    for delta in (1,'1/2'):
        case=fractional_gap(delta); b=case['bundles'][0];q={c['id']:c['quota'] for c in case['contacts']}
        p=search(case,b,q,case['background']);o=solve(case,b,q,case['background'])
        assert p['arrival']==o['arrival']
        gap.append(dict(delta=case['delta'],input=case,proposed=p,oracle=o))
    write('counterexample_grid_continuous.json',dict(classification='model-boundary witness, not frozen-grid defect',runs=gap))
    write('comparison_gate.json',dict(status='PASS_FINITE_CASES',queries=len(records),algorithm_changed=False,
                                      timing_benchmarks=False,continuous_optimality=False))
    print('Oracle matched',len(records),'queries;',[(str(x['delta']),str(x['proposed']['arrival'])) for x in gap])

if __name__=='__main__':run()
