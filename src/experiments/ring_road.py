"""Bounded experiments using the unchanged frozen v04 router and public RRN data.

Keep downloaded inputs and verbose traces local; publish compact measurements only.
All data units use decimal MB. A timeout is an unfinished case, never NO_ROUTE.
"""
import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from statistics import mean, pstdev

from .config import load_scenario
from .runner import write_json, write_csv

SOURCE = ('https://api.bitbucket.org/2.0/repositories/lcd-unc-ar/dtnsim/src/'
          '56d2c9835f6706563566768de646f9442a8602ab/dtnsim/simulations/hindawi_rrn/'
          'contactPlan/RingRoad_16sats_Walker_6hotspots_simtime24hs_comrange1000km.txt')
EXPECTED_SHA = 'fe363dabdd182e292f5e3b74a28558245b2caf9d3aa7730db60d52afdb9763d2'


def convert_contacts(path, horizon, rate_MB_s):
    """Retain original directed contacts, remove EID 48, clip at the stated horizon."""
    contacts = []
    original_index = 0
    for line in Path(path).read_text(encoding='utf8').splitlines():
        fields = line.split()
        if fields[:2] != ['a', 'contact']:
            continue
        original_index += 1
        _, _, start, end, source, target, _ = fields
        if '48' in (source, target):
            continue
        start, end = F(start), min(F(end), F(horizon))
        if start >= end:
            continue
        contacts.append(dict(id=f'rrn_{original_index:04d}', source=source,
                             target=target, start=str(start), end=str(end),
                             rate=str(F(rate_MB_s)), delay='0'))
    return contacts


def prepare(source, folder, profile='day'):
    """Predeclare all scenarios; repeated size/load cases reuse seed and prefixes."""
    folder.mkdir(parents=True, exist_ok=False)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError(f'Unexpected source SHA-256: {digest}')
    rng = random.Random(20261011)
    demands = [(str(rng.randint(7, 31)), str(rng.randint(1, 6)), rng.randint(0, 300))
               for _ in range(10)]
    # Anchor explicitly exercises a satellite -> hot spot; random traffic is separate.
    anchor = [('36', '6', 400)]
    specs = [
        ('pilot_satellite_900', 900, '1/80', '3/10', 30, anchor),
        ('pilot_cold_900', 900, '1/80', '3/10', 30, demands[:1]),
        ('original_day_n1', 86400, '1/80', '3/10', 30, demands[:1]),
        ('original_day_n5', 86400, '1/80', '3/10', 30, demands[:5]),
        ('original_day_n10', 86400, '1/80', '3/10', 30, demands),
        ('thesis_rate_day_n1', 86400, '1/10', '3/10', 30, demands[:1]),
        ('thesis_rate_day_n5', 86400, '1/10', '3/10', 30, demands[:5]),
        ('thesis_rate_day_n10', 86400, '1/10', '3/10', 30, demands),
        ('size_600KB_day_n5', 86400, '1/80', '3/5', 30, demands[:5]),
        ('size_1200KB_day_n5', 86400, '1/80', '6/5', 30, demands[:5]),
        ('buffer_300KB_day_n5', 86400, '1/80', '3/10', '3/10', demands[:5]),
        ('buffer_600KB_day_n5', 86400, '1/80', '3/10', '3/5', demands[:5]),
    ]
    if profile in ('short', 'full_stress'):
        # Explicit stress cases, not random traffic or a claim of representative load.
        shared = anchor * 10
        cold = [('22', '5', 253)] * 5
        specs = [
            ('sat_900_n1', 900, '1/80', '3/10', 30, shared[:1]),
            ('sat_900_n5', 900, '1/80', '3/10', 30, shared[:5]),
            ('sat_900_n10', 900, '1/80', '3/10', 30, shared),
            ('sat_900_size600_n5', 900, '1/80', '3/5', 30, shared[:5]),
            ('sat_900_size1200_n5', 900, '1/80', '6/5', 30, shared[:5]),
            ('sat_900_buffer300_n5', 900, '1/80', '3/10', '3/10', shared[:5]),
            ('sat_900_buffer600_n5', 900, '1/80', '3/10', '3/5', shared[:5]),
            ('sat_900_thesisrate_n5', 900, '1/10', '3/10', 30, shared[:5]),
            ('cold_1800_n1', 1800, '1/80', '3/10', 30, cold[:1]),
            ('cold_1800_n5', 1800, '1/80', '3/10', 30, cold),
            ('cold_transit_buffer300_n5', 1800, '1/80', '3/10', 30, cold),
            ('cold_transit_buffer600_n5', 1800, '1/80', '3/10', 30, cold),
        ]
        if profile == 'full_stress':
            specs = [(name.replace('_900_', '_day_').replace('_1800_', '_day_'),
                      86400, rate, size, buffer, traffic)
                     for name, _, rate, size, buffer, traffic in specs]
    entries = []
    for name, horizon, rate, size, buffer, traffic in specs:
        config = dict(schema_version=1, name=name,
                      description='Frozen v04; enumeration; zero propagation delay assumption',
                      units=dict(time='s', data='MB', rate='MB/s'),
                      time_step='1', horizon=str(horizon),
                      nodes=[dict(id=str(n), buffer=str(buffer)) for n in range(1, 48)],
                      contacts=convert_contacts(source, horizon, rate),
                      bundles=[dict(id=f'b{i:03d}', source=u, destination=v,
                                    release=str(g), size=size)
                               for i, (u, v, g) in enumerate(traffic, 1)])
        if name.startswith('cold_transit_buffer'):
            transit_buffer = '3/10' if 'buffer300' in name else '3/5'
            next(n for n in config['nodes'] if n['id'] == '37')['buffer'] = transit_buffer
        path = folder / f'{name}.json'
        write_json(path, config)
        load_scenario(path)  # Reject alignment/unit errors before any run.
        entries.append(dict(name=name, config=str(path.resolve()), horizon=horizon,
                            rate_MB_s=rate, size_MB=size, buffer_MB=str(buffer),
                            requested=len(traffic), contacts=len(config['contacts']),
                            traffic=('explicit_shared_contact_stress' if profile in ('short', 'full_stress')
                                     else 'anchor' if traffic == anchor else 'seeded_random'),
                            demands=config['bundles']))
        entries[-1]['node_buffer_overrides_MB'] = (
            {'37': transit_buffer} if name.startswith('cold_transit_buffer') else {})
    metadata = dict(source_url=SOURCE, source_sha256=digest, seed=20261011,
                    model='frozen_v04_internal_usage_cache_time_enumeration',
                    grid_s=1, propagation_delay_s=0, server_48_removed=True,
                    decimal_MB=True, deadlines=False, joint_optimization=False,
                    transmission_calendar=False, profile=profile, cases=entries)
    write_json(folder / 'manifest.json', metadata)
    return metadata


def worker(config, output, compact=False):
    """Time search only; preserve the engine and its independent feasibility checks."""
    from . import runner
    case = load_scenario(config)
    output = Path(output)
    search = runner.search
    if compact:
        from functools import partial
        from .compact_search import search as compact_search
        execute_search = partial(compact_search, trace_events=False)
    else:
        execute_search = search

    def measured_search(case, bundle, quota, background, dominance=True):
        started = time.perf_counter()
        result = execute_search(case, bundle, quota, background, dominance=dominance)
        elapsed = time.perf_counter() - started
        diagnostics = result.get('diagnostics', {})
        events = Counter(diagnostics.get('events', Counter(row['event'] for row in result['trace'])))
        reasons = Counter(diagnostics.get('reasons', Counter(row.get('reason', '')
                          for row in result['trace'] if row['event'] == 'EXTEND')))
        valid_candidates = max(0, result['stats']['created'] - 1)
        row = dict(bundle=bundle['id'], search_wall_s=elapsed, **result['stats'],
                   start_times_tested=events['EXTEND'], buffer_rejected=reasons['BUFFER'],
                   source_buffer_rejected=events['SOURCE_FAIL'],
                   contact_quota_rejected=events['CONTACT_QUOTA_FAIL'],
                   contact_time_rejected=events['CONTACT_TIME_FAIL'],
                   max_queue_records=diagnostics.get('max_queue_records', max((
                       e.get('queue_count', len(e.get('queue_after', [])))
                       for e in result['trace']), default=0)),
                   pruned_new_ratio=(result['stats']['pruned_new'] / valid_candidates
                                     if valid_candidates else None))
        # Write immediately, retaining completed-query evidence if a later query times out.
        write_json(output / f'measure_{bundle["id"]}.json', row)
        return result

    runner.search = measured_search
    try:
        result = runner.run_scenario(case, output, verify_oracle=False)
    finally:
        runner.search = search
    from .report import analyze
    replay = analyze(case, result)
    for key in ('routes', 'schedules', 'buffer_peaks', 'link_conflicts'):
        write_json(output / f'{key}.json', replay[key])
    used_nodes = {hop[k] for hop in replay['schedules'] for k in ('sender', 'receiver')}
    samples = [r for r in replay['buffer_samples'] if r['node'] in used_nodes]
    if samples:
        write_csv(output / 'buffer_samples.csv', list(samples[0]), samples)


def describe(values):
    return dict(mean=mean(values), minimum=min(values), maximum=max(values),
                population_std=pstdev(values)) if values else None


def destination_lower_bound(case, bundle, quota):
    """Relax all prefix/buffer constraints; every valid route needs a last contact.

    Equality with a validated route certifies that query's optimum. A positive
    gap is only a gap to this bound, not an error relative to the true optimum.
    """
    arrivals = []
    for edge in case['contacts']:
        if edge['v'] != bundle['dest'] or F(quota[edge['id']]) < bundle['size']:
            continue
        finish = max(bundle['g'], edge['start']) + bundle['size']/edge['rate']
        arrival = finish + edge['delay']
        if finish <= edge['end'] and arrival <= case['horizon']:
            arrivals.append(arrival)
    return min(arrivals) if arrivals else None


def read_complete_json_files(folder, pattern):
    records, incomplete = [], []
    for path in sorted(folder.glob(pattern)):
        try:
            records.append(json.loads(path.read_text(encoding='utf8')))
        except (json.JSONDecodeError, UnicodeError):
            incomplete.append(path.name)
    return records, incomplete


def export_partial_queries(local, output):
    """Preserve individually validated queries without estimating case acceptance."""
    records, _ = read_complete_json_files(local, 'query_*.json')
    if not records:
        return
    case = load_scenario(local / 'input.json')
    edges = {e['id']: e for e in case['contacts']}
    summaries, schedules = [], []
    for record in records:
        bundle = record['bundle']
        summaries.append(dict(bundle=bundle['id'], source=bundle['source'],
            destination=bundle['dest'], status=record['status'], arrival=record['arrival'],
            note='PARTIAL_CASE; no overall acceptance inferred'))
        for index, (cid, start) in enumerate(record['hops'], 1):
            edge, start = edges[cid], F(start)
            finish = start+F(bundle['size'])/edge['rate']
            schedules.append(dict(bundle=bundle['id'], hop=index, contact=cid,
                sender=edge['u'], receiver=edge['v'], start=str(start), finish=str(finish),
                arrival=str(finish+edge['delay'])))
    write_csv(output / 'partial_summary.csv', list(summaries[0]), summaries)
    if schedules:
        write_csv(output / 'partial_schedule.csv', list(schedules[0]), schedules)


def execute(source, output, budget_s, profile='day', selected=None, compact=False):
    from shutil import copyfile
    output.mkdir(parents=True, exist_ok=False)
    local = Path('tmp/ring_road_runs') / output.name
    local.mkdir(parents=True, exist_ok=False)
    manifest = prepare(source, local / 'configs', profile)
    if selected:
        requested = set(selected)
        existing = {entry['name'] for entry in manifest['cases']}
        if requested - existing:
            raise ValueError(f'Unknown cases: {sorted(requested-existing)}')
        manifest['cases'] = [e for e in manifest['cases'] if e['name'] in requested]
    public_manifest = dict(manifest, cases=[{k: v for k, v in e.items() if k != 'config'}
                                          for e in manifest['cases']],
                           per_case_wall_budget_s=budget_s)
    public_manifest['execution_adapter'] = 'compact_same_rules' if compact else 'literal_full_trace'
    write_json(output / 'manifest.json', public_manifest)
    rows, measurements = [], []
    write_json(output / 'status.json', dict(status='RUNNING'))
    for entry in manifest['cases']:
        target = local / entry['name']
        started = time.perf_counter()
        with (local / f'{entry["name"]}.log').open('w', encoding='utf8') as log:
            command = [sys.executable, '-m', 'src.experiments.ring_road',
                       '--worker', entry['config'], str(target)]
            if compact:
                command.append('--compact')
            child = subprocess.Popen(command,
                                     stdout=log, stderr=log)
            try:
                code = child.wait(timeout=budget_s)
                state = 'COMPLETE' if code == 0 else 'ERROR'
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait()
                state = 'TIMEOUT'
        status_path = target / 'status.json'
        status = json.loads(status_path.read_text(encoding='utf8')) if status_path.exists() else {}
        if status.get('status') == 'STOP' or state == 'ERROR':
            write_json(output / 'status.json', dict(status='STOP', case=entry['name'],
                       reason=status, local_evidence=str(target.resolve())))
            raise RuntimeError(f'Stopped; inspect {target}')
        case_output = output / entry['name']
        case_output.mkdir()
        if state == 'TIMEOUT':
            export_partial_queries(target, case_output)
        metrics, incomplete_measures = read_complete_json_files(target, 'measure_*.json')
        measurements.extend(dict(case=entry['name'], **m) for m in metrics)
        completed_records, incomplete_queries = read_complete_json_files(target, 'query_*.json')
        complete_queries = len(completed_records)
        row = dict(case=entry['name'], status=state, requested=entry['requested'],
                   completed_queries=complete_queries, measured_searches=len(metrics),
                   wall_s=time.perf_counter()-started, horizon_s=entry['horizon'],
                   contacts=entry['contacts'], rate_MB_s=entry['rate_MB_s'],
                   size_MB=entry['size_MB'], buffer_MB=entry['buffer_MB'],
                   accepted=None, acceptance_ratio=None, delay_mean_s=None,
                   delay_min_s=None, delay_max_s=None, delay_population_std_s=None,
                   search_wall_mean_s=None, labels_created_total=None,
                   search_wall_min_s=None, search_wall_max_s=None,
                   search_wall_population_std_s=None,
                   pruned_new_total=None, buffer_peak_MB=None, contact_overlap_count=None,
                   earliest_arrival_oracle_checked=False)
        if state == 'COMPLETE':
            results = json.loads((target / 'results.json').read_text(encoding='utf8'))
            delays = [float(F(r['arrival'])-F(r['bundle']['g']))
                      for r in results['records'] if r['status'] == 'ACCEPTED']
            stats = describe(delays)
            times = describe([m['search_wall_s'] for m in metrics])
            row.update(accepted=len(delays), acceptance_ratio=len(delays)/entry['requested'],
                       delay_mean_s=stats['mean'] if stats else None,
                       delay_min_s=stats['minimum'] if stats else None,
                       delay_max_s=stats['maximum'] if stats else None,
                       delay_population_std_s=stats['population_std'] if stats else None,
                       search_wall_mean_s=mean(m['search_wall_s'] for m in metrics),
                       search_wall_min_s=times['minimum'], search_wall_max_s=times['maximum'],
                       search_wall_population_std_s=times['population_std'],
                       labels_created_total=sum(m['created'] for m in metrics),
                       pruned_new_total=sum(m['pruned_new'] for m in metrics),
                       buffer_peak_MB=max(float(F(p['peak'])) for p in
                           json.loads((target / 'buffer_peaks.json').read_text(encoding='utf8'))),
                       contact_overlap_count=len(json.loads(
                           (target / 'link_conflicts.json').read_text(encoding='utf8'))))
            for name in ('summary.csv', 'schedule.csv', 'routes.json', 'buffer_peaks.json',
                         'link_conflicts.json'):
                copyfile(target / name, case_output / name)
            if (target / 'buffer_samples.csv').exists():
                copyfile(target / 'buffer_samples.csv', case_output / 'buffer_samples.csv')
            hop_metrics = []
            case = load_scenario(entry['config'])
            edges = {e['id']: e for e in case['contacts']}
            for bundle, record in zip(case['bundles'], results['records']):
                accepted = record['status'] == 'ACCEPTED'
                transmission = sum((F(record['bundle']['size']) / edges[cid]['rate']
                                    for cid, _ in record['hops']), F(0))
                delay = (F(record['arrival'])-F(record['bundle']['g'])) if accepted else None
                bound = destination_lower_bound(case, bundle, record['quota_before'])
                hop_metrics.append(dict(bundle=record['bundle']['id'], status=record['status'],
                    hops=len(record['hops']) if accepted else None,
                    total_transmission_s=str(transmission) if accepted else None,
                    total_waiting_s=str(delay-transmission) if accepted else None,
                    arrival_lower_bound_s=str(bound) if bound is not None else None,
                    arrival_gap_to_lower_bound_s=str(F(record['arrival'])-bound)
                        if accepted and bound is not None else None,
                    earliest_arrival_certified_by_bound=bool(accepted and bound == F(record['arrival'])),
                    no_route_certified_by_no_last_contact=bool(not accepted and bound is None)))
            write_csv(case_output / 'bundle_time_breakdown.csv', list(hop_metrics[0]), hop_metrics)
        write_json(case_output / 'measurements.json', metrics)
        write_json(case_output / 'status.json', dict(status=state,
                   completed_queries=complete_queries, wall_budget_s=budget_s,
                   no_route_inferred_from_timeout=False, original_status=status))
        if incomplete_measures or incomplete_queries:
            write_json(case_output / 'incomplete_json_files.json',
                       dict(files=incomplete_measures+incomplete_queries,
                            raw_files_retained_locally=True, counted_as_completed=False))
        rows.append(row)
        write_csv(output / 'case_summary.csv', list(row), rows)
        if measurements:
            write_csv(output / 'search_measurements.csv', list(measurements[0]), measurements)
        print(f'{entry["name"]}: {state}; queries={complete_queries}/{entry["requested"]}', flush=True)
    write_json(output / 'status.json', dict(status='COLLECTION_COMPLETE',
        complete_cases=sum(r['status']=='COMPLETE' for r in rows),
        timeout_cases=sum(r['status']=='TIMEOUT' for r in rows),
        independent_schedule_check=True, earliest_arrival_oracle_checked=False,
        performance_comparison_run=False, physical_simulation=False))
    lines = ['# Ring Road 初步實驗', '',
        '既有 frozen v04（含 usage cache、時間枚舉）。不是移除 U 後的新實作。',
        f'Profile={profile}；decimal MB；零傳播延遲假設；固定目的地；依需求清單順序規劃。',
        'day使用固定seed 20261011；short/full_stress為預先列出的共用Contact壓力案例，不是隨機代表性流量。',
        '每案例使用獨立程序及相同時間上限。TIMEOUT 不能當成無路徑或拒絕。',
        '完整案例通過獨立排程、資源更新與 Buffer 回放；未對此大型拓樸執行完整搜尋證明最早到達。', '',
        '| 案例 | 狀態 | 完成查詢/需求 | 接受包數 | 平均送達延遲(s) | Label數 |',
        '|---|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f'| {r["case"]} | {r["status"]} | {r["completed_queries"]}/{r["requested"]} | '
                     f'{r["accepted"]} | {r["delay_mean_s"]} | {r["labels_created_total"]} |')
    lines += ['', '## 解讀限制', '',
        '- 原檔速率 0.0125 MB/s，論文速率組採 decimal 0.1 MB/s；不是單位等價。',
        '- 900秒案例只是截取前段且以900秒作交付上限；不能替代一天結果。',
        '- 學長處理多 Flow 聯合最佳化與各自 deadline；本實驗為固定目的地、不可分割 Bundle、逐包預約，因此不是重現學長效能。',
        '- 採相同隨機需求前綴比較需求數，大小實驗沿用相同來源/目的地/生成時間；僅一個seed，不能做一般統計推論。',
        '- 不比較其他演算法，不能據此宣稱優勢；剪枝比例只是搜尋工作量描述。',
        '- 原始需求所需資料量、速率、Buffer與時間範圍詳見manifest；路徑與傳送時間見各案例schedule.csv。',
        '- 平均/最小/最大/母體標準差只對已接受包計算；沒有已知最優值時，最優誤差及誤差百分比為未取得，不填零。',
        '- bundle_time_breakdown的arrival_lower_bound_s忽略路徑前綴及Buffer，只看可承載整包的最後一跳；已驗證路徑等於此下界時，僅該查詢可證最早抵達。正差值不是對真實最優值的誤差。',
        '- Contact時段重疊是aggregate模型的已知物理限制，必須同時報告；不是已驗證可實際執行的網路排程。',
        '- 全量輸入及原始trace保留於tmp/ring_road_runs；正式輸出只保存摘要，未重新發布第三方Contact Plan。']
    (output / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', nargs=2, metavar=('CONFIG', 'OUTPUT'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--budget', type=float, default=20)
    parser.add_argument('--profile', choices=['day', 'short', 'full_stress'], default='day')
    parser.add_argument('--case', action='append', help='Only run this named case (repeatable)')
    parser.add_argument('--compact', action='store_true', help='Same rules, indexed lookup and compact trace')
    args = parser.parse_args()
    if args.worker:
        worker(*args.worker, compact=args.compact)
    else:
        if not args.source or not args.output or args.budget <= 0:
            parser.error('--source, --output and positive --budget required')
        execute(args.source, args.output, args.budget, args.profile, args.case, args.compact)


if __name__ == '__main__':
    main()
