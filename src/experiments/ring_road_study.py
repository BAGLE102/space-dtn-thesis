"""Consolidate explicit attempts; retain timeouts and their provenance."""
import argparse
import csv
import json
from pathlib import Path
from shutil import copyfile

from .runner import write_csv, write_json


def validate_artifacts(full, short, output):
    from fractions import Fraction as F
    checked, queries, timeouts = 0, 0, 0
    for folder, filename in ((full, 'case_summary.csv'), (short, 'case_summary.csv')):
        with (folder / filename).open(encoding='utf-8-sig') as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            case = folder / row['case']
            checked += 1
            if row['status'] == 'TIMEOUT':
                assert row['accepted'] == row['acceptance_ratio'] == ''
                timeouts += 1
                continue
            assert row['status'] == 'COMPLETE'
            with (case/'summary.csv').open(encoding='utf-8-sig') as stream:
                bundles = list(csv.DictReader(stream))
            assert len(bundles) == int(row['requested']) == int(row['completed_queries'])
            assert sum(b['status']=='ACCEPTED' for b in bundles) == int(row['accepted'])
            measurements = json.loads((case/'measurements.json').read_text(encoding='utf8'))
            assert len(measurements) == len(bundles)
            for m in measurements:
                assert m['created'] == m['enqueued']+m['pruned_new']
                assert m['expanded'] <= m['enqueued']
            for peak in json.loads((case/'buffer_peaks.json').read_text(encoding='utf8')):
                assert F(peak['peak']) <= F(peak['limit'])
            conflicts = json.loads((case/'link_conflicts.json').read_text(encoding='utf8'))
            assert len(conflicts) == int(row['contact_overlap_count'])
            with (case/'bundle_time_breakdown.csv').open(encoding='utf-8-sig') as stream:
                for b in csv.DictReader(stream):
                    if b['status'] == 'ACCEPTED':
                        assert F(b['total_waiting_s']) >= 0
                        assert F(b['arrival_gap_to_lower_bound_s']) >= 0
            queries += len(bundles)
    write_json(output, dict(status='PASS', checked_cases=checked,
        complete_query_records=queries, timeout_cases=timeouts,
        acceptance_counts=True, label_counter_identity=True,
        buffer_peaks_within_limits=True, overlap_counts_preserved=True,
        physical_conflicts_required_to_be_zero=False))


def consolidate(runs, short, output, random_run=None):
    output.mkdir(parents=True, exist_ok=False)
    latest, attempts = {}, []
    for run in runs:
        status = json.loads((run / 'status.json').read_text(encoding='utf8'))
        if status['status'] != 'COLLECTION_COMPLETE':
            raise ValueError(f'Incomplete collection: {run}')
        with (run / 'case_summary.csv').open(encoding='utf-8-sig') as stream:
            for row in csv.DictReader(stream):
                row = dict(row, source_run=run.name)
                attempts.append(row)
                latest[row['case']] = (run, row)
    fields = list(dict.fromkeys(key for row in attempts for key in row))
    write_csv(output / 'all_attempts.csv', fields, attempts)
    rows, complete, timed_out, certified, accepted_total = [], 0, 0, 0, 0
    for name, (run, row) in latest.items():
        rows.append(row)
        if row['status'] == 'COMPLETE':
            complete += 1
            accepted_total += int(row['accepted'])
        else:
            timed_out += 1
        target = output / 'full_day' / name
        target.mkdir(parents=True)
        for file in (run / name).iterdir():
            if file.suffix in ('.csv', '.json'):
                copyfile(file, target / file.name)
        breakdown = target / 'bundle_time_breakdown.csv'
        if breakdown.exists():
            with breakdown.open(encoding='utf-8-sig') as stream:
                certified += sum(r['earliest_arrival_certified_by_bound'] == 'True'
                                 for r in csv.DictReader(stream))
    write_csv(output / 'full_day_summary.csv', fields, rows)
    write_csv(output / 'full_day' / 'case_summary.csv', fields, rows)
    copyfile(short / 'case_summary.csv', output / 'short_window_summary.csv')
    if random_run:
        random_status = json.loads((random_run / 'status.json').read_text(encoding='utf8'))
        if random_status['status'] != 'COLLECTION_COMPLETE':
            raise ValueError(f'Incomplete random collection: {random_run}')
        copyfile(random_run / 'case_summary.csv', output / 'random_demand_summary.csv')
        copyfile(random_run / 'manifest.json', output / 'random_demand_manifest.json')
    source_manifest = json.loads((runs[0] / 'manifest.json').read_text(encoding='utf8'))
    for entry in source_manifest['cases']:
        entry.pop('config', None)
    write_json(output / 'protocol_manifest.json', source_manifest)
    write_json(output / 'status.json', dict(status='CONSOLIDATED',
        full_day_complete_cases=complete, full_day_timeout_cases=timed_out,
        accepted_in_complete_cases=accepted_total,
        accepted_certified_by_lower_bound=certified,
        all_full_day_cases_complete=timed_out == 0,
        same_model_independent_checks_passed=True,
        general_optimality_proven=False, physical_calendar_checked=False,
        full_day_runs=[p.name for p in runs], short_window_run=short.name))
    lines = ['# Ring Road 實驗結果整理', '',
        f'完整一天、3,172 條 Contact：{complete} 組完成、{timed_out} 組逾時。',
        '這裡的「完成」指該設定全部 Bundle 的搜尋、獨立排程與資源檢查均完成；不代表完成整篇論文的實驗或已證明方法優勢。',
        '採原 frozen v04 的判別式及時間枚舉，精簡版只調整索引及紀錄。內部仍保留 usage cache。', '',
        '| 案例 | 狀態 | 完成查詢/需求 | 模型接受包數 | 平均延遲(s) | Contact重疊對數 |',
        '|---|---|---:|---:|---:|---:|']
    for row in rows:
        show = lambda key: row.get(key) or '—'
        lines.append(f'| {row["case"]} | {row["status"]} | '
                     f'{row["completed_queries"]}/{row["requested"]} | '
                     f'{show("accepted")} | {show("delay_mean_s")} | {show("contact_overlap_count")} |')
    lines += ['', '## 未完成部分', '']
    for row in rows:
        if row['status'] == 'TIMEOUT':
            state = json.loads((output/'full_day'/row['case']/'status.json').read_text(encoding='utf8'))
            lines.append(f'- {row["case"]}：上限{state["wall_budget_s"]}秒，'
                         f'僅完成{row["completed_queries"]}/{row["requested"]}筆查詢；'
                         '已驗證的部分路徑另存partial_summary.csv／partial_schedule.csv。不能推論其餘無路徑。')
    if random_run:
        with (random_run/'case_summary.csv').open(encoding='utf-8-sig') as stream:
            random_rows = list(csv.DictReader(stream))
        lines.append(f'- 隨機需求重試：{sum(r["status"]=="COMPLETE" for r in random_rows)}組完成、'
                     f'{sum(r["status"]=="TIMEOUT" for r in random_rows)}組逾時。'
                     '完整設定與完成查詢數見random_demand_summary.csv；不能用固定來源的成功案例取代此結果。')
    lines.append('- 尚未完成學長50–175條Flow的規模、多seed／重複計時或與CGR／opt的公平比較；本次不是完整論文效能評估。')
    lines += ['', '## 如何使用這些結果', '',
        '- 衛星36→6案例顯示容量不足後改走中繼衛星，以及需求量、Bundle大小、速率對路徑和延遲的影響。',
        '- 冷點22→5案例顯示只降低中繼37 Buffer時，後續Bundle可改走36並較晚抵達；短窗口可能拒絕，全日窗口可能找到替代路徑。逐包結果見各組routes.json。',
        '- Buffer很小且所有節點一起降低時，可能在來源生成就拒絕；不能全部說成中繼Buffer效果。另有僅降低37的組別作診斷。',
        '- 同Contact重疊仍存在，接受比例不等於實際網路送達率。不能拿這些接受結果直接宣稱比CGR好。',
        f'- 完成組共接受{accepted_total}包，其中{certified}包達到獨立最後一跳下界，可就該查詢確認最早抵達；其餘沒有本次的最優證明。',
        '- 下界只忽略前綴與Buffer；對其差距不等於對真正最優解的誤差。未執行全日完整搜尋oracle。',
        '- 逾時不當成無路徑；未完成組不計整組接受比例或延遲平均值。先前嘗試與所有逾時紀錄保留於all_attempts.csv。',
        '- wall time來自本機單次／有併行負載的初步執行，只作規模診斷，不能作正式加速比或統計顯著性結論。',
        '- 固定來源的壓力案例不是一般隨機流量；隨機需求試跑與重試另存，不能以這些成功案例取代隨機流量結論。', '',
        '## 檔案', '',
        '- full_day_summary.csv：每組設定、完成狀態、延遲統計、Label總數、Buffer峰值與重疊。',
        '- full_day/<case>/summary.csv、schedule.csv、routes.json：每包路徑、抵達及各跳時間。',
        '- full_day/<case>/measurements.json：每包搜尋時間、剪枝、時間嘗試及失敗分類。',
        '- full_day/<case>/bundle_time_breakdown.csv：傳輸／等待時間與最早抵達下界。',
        '- full_day/<case>/buffer_samples.csv、buffer_peaks.json、link_conflicts.json：Buffer曲線及物理限制診斷。',
        '- short_window_summary.csv：短窗口對照；完整短窗口資料保留在原run。',
        '- random_demand_summary.csv／random_demand_manifest.json：隨機需求重試（若提供），與壓力案例分開。',
        '- protocol_manifest.json：明列全部壓力案例需求、節點Buffer例外及來源hash。', '',
        '研究方法、假設、與學長的差異及重現命令見docs/ring_road_experiment_protocol_v01.md。']
    (output / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', type=Path, required=True,
                        help='Explicit attempts in chronological order')
    parser.add_argument('--short', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--random-run', type=Path)
    args = parser.parse_args()
    consolidate(args.run, args.short, args.output, args.random_run)
    validate_artifacts(args.output/'full_day', args.short,
                       args.output/'artifact_checks.json')
