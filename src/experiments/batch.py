"""Run small, reproducible correctness experiments without changing routing."""
import argparse
import json
from fractions import Fraction
from pathlib import Path
from statistics import mean, pstdev

from .config import load_scenario
from .runner import run_scenario, write_csv, write_json, CorrectnessFailure
from .report import generate


def run_batch(manifest_path, output, figures=False):
    manifest_path, output = Path(manifest_path), Path(output)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'manifest.json', manifest)
    write_json(output/'status.json', {'status':'RUNNING'})
    case_rows, bundle_rows = [], []
    try:
        for entry in manifest['cases']:
            case = load_scenario(manifest_path.parent / entry['config'])
            target = output / case['name']
            result = run_scenario(case, target, verify_oracle=True)
            generate(target, draw=False)
            report_path = target/'report'/'report.md'
            report_path.write_text(report_path.read_text(encoding='utf8').replace(
                '# PPT拓樸執行結果', '# ' + entry['description'], 1), encoding='utf8', newline='\n')
            check = json.loads((target/'report'/'replay_check.json').read_text(encoding='utf8'))
            arrivals = [None if r['arrival'] is None else str(r['arrival']) for r in result['records']]
            expected = entry['expected_arrivals']
            conflicts = len(check['link_conflicts'])
            if arrivals != expected or conflicts != entry['expected_contact_conflicts']:
                write_json(target/'expectation_failure.json',dict(actual_arrivals=arrivals,
                    expected_arrivals=expected, actual_conflicts=conflicts, entry=entry))
                raise CorrectnessFailure(f"Case expectation mismatch: {case['name']}")
            delays = []
            for record in result['records']:
                bundle = record['bundle']
                contacts = {c['id']:c for c in case['contacts']}
                nodes = [bundle['source']] + [contacts[c]['v'] for c,s in record['hops']]
                delay = None if record['arrival'] is None else record['arrival']-bundle['g']
                if delay is not None:
                    delays.append(float(delay))
                bundle_rows.append(dict(case=case['name'],bundle=bundle['id'],
                    status=record['status'],node_path=' → '.join(nodes) if delay is not None else '',
                    contacts=' → '.join(c for c,s in record['hops']),arrival=record['arrival'],
                    delay=delay,labels_created=record['stats']['created'],
                    labels_expanded=record['stats']['expanded'],
                    labels_pruned=record['stats']['pruned_new']+record['stats']['pruned_old'],
                    oracle_checked=True,arrival_error_s=0 if delay is not None else None))
            accepted=len(delays)
            case_rows.append(dict(case=case['name'],description=entry['description'],
                requested=len(result['records']),accepted=accepted,
                acceptance_ratio=accepted/len(result['records']),
                delay_mean_s=mean(delays) if delays else None,
                delay_min_s=min(delays) if delays else None,
                delay_max_s=max(delays) if delays else None,
                delay_population_std_s=pstdev(delays) if delays else None,
                labels_created=sum(r['stats']['created'] for r in result['records']),
                buffer_peak_MB=max(Fraction(p['peak']) for p in check['buffer_peaks']),
                contact_overlap_count=conflicts,oracle_match=True,expected_match=True))
            print(f"{case['name']}: accepted={accepted}, arrivals={arrivals}, conflicts={conflicts}",flush=True)
            if figures and case['name']=='01_ppt_baseline':
                from .report import analyze, render
                positions_path=manifest_path.parent.parent/'walkthrough_positions.json'
                positions=json.loads(positions_path.read_text(encoding='utf8'))
                render(case,analyze(case,result),target/'report',positions)
    except Exception as error:
        write_json(output/'status.json',dict(status='STOP',error=str(error),performance_comparison_allowed=False))
        write_json(output/'partial_results.json',dict(cases=case_rows,bundles=bundle_rows))
        raise
    write_csv(output/'case_summary.csv',list(case_rows[0]),case_rows)
    write_csv(output/'bundle_summary.csv',list(bundle_rows[0]),bundle_rows)
    lines=['# 小型路由驗證實驗 v01','',
        '本次使用含內部 usage cache 的 frozen v04，保留時間枚舉；不是移除 U 後的新實作，也沒有使用 SimPy。',
        '所有案例均啟用獨立完整搜尋、完整排程與資源更新檢查。這是案例驗證，不是一般正確性證明或效能比較。','',
        '| 案例 | 設定 | 接受包數 | 依規劃順序的抵達時間（秒） | 同 contact 重疊數 |',
        '|---|---|---:|---|---:|']
    for row in case_rows:
        actual=[str(r['arrival']) if r['arrival'] is not None else '無路徑' for r in bundle_rows if r['case']==row['case']]
        lines.append(f"| {row['case']} | {row['description']} | {row['accepted']}/{row['requested']} | {', '.join(actual)} | {row['contact_overlap_count']} |")
    lines += ['', '## 結果解讀','',
        '- B容量增加至8MB時，本案例可讓第二包較早進入B等待，但不一定改善目的地抵達時間。實際路徑見bundle_summary.csv。',
        '- c1容量不足時，第一包未接受，便不會預約c2，第二包可提早抵達。這不是容量降低通常有利的結論。',
        '- 固定處理順序會改變資源分配；反轉案例保留原生成時間，是規劃順序敏感度檢查。',
        '- 09是已知模型限制：總容量模型接受兩包，但同contact的發送時段重疊。未移動發送時間或修改路由規則，不能宣稱實體鏈路可執行。',
        '- 格點變細後此案例抵達時間相同，不代表所有案例相同。',
        '- delay統計僅含已接受的bundles；無路徑不以0秒代替。標準差採母體標準差。沒有執行時間或方法優劣的統計推論。',
        '- 接受路徑相對獨立完整搜尋的抵達時間誤差皆為0；比率誤差不對零值強行計算。','',
        '## 檔案','',
        '- case_summary.csv：案例統計。',
        '- bundle_summary.csv：每包路徑、抵達時間、延遲與Label數量。',
        '- 各案例/report/：事件、Buffer峰值、排程重播與同contact重疊檢查。',
        '- 各案例/query_*.json：完整Label與Q事件紀錄。',
        '- 01_ppt_baseline/report/：加上 --figures 時產生PPT路徑與Buffer圖。','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf8',newline='\n')
    write_json(output/'status.json',dict(status='COMPLETE',cases=len(case_rows),
        bundles=len(bundle_rows),oracle_match=True,expected_match=True,
        internal_usage_cache=True,simpy_used=False,performance_comparison_run=False,
        known_model_boundary_cases=['09_aggregate_overlap']))
    return output


def main():
    parser=argparse.ArgumentParser(description='批次執行小型路由驗證實驗')
    parser.add_argument('--manifest',type=Path,default=Path('configs/experiments_v01/manifest.json'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--figures',action='store_true',help='產生基準案例圖；需要matplotlib')
    args=parser.parse_args()
    print(run_batch(args.manifest,args.output,args.figures))


if __name__=='__main__':
    main()
