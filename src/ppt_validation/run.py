"""小案例驗證入口與報表，不做效能比較、不改 frozen v04。"""
import argparse
from collections import Counter
from copy import deepcopy
import csv
from fractions import Fraction as F
import json
from pathlib import Path
import statistics

from src.experiments.config import load_scenario, validate_case
from src.validation.model import commit, jsonable, occupancy, route_curves
from src.validation.exhaustive_oracle import commit_independently, background_at
from .search import search
from .reference import evaluate, solve


def write_json(path, obj):
    Path(path).write_text(json.dumps(jsonable(obj), ensure_ascii=False, indent=2)+'\n',
                          encoding='utf-8', newline='\n')


def write_csv(path, fields, rows):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(jsonable(rows))


def breakpoints(background, horizon):
    return sorted({F(0), horizon} | {t for curves in background.values()
                  for curve in curves for segment in curve for t in segment[:2]})


def buffer_rows(case, background, query):
    """折點數值供核對；曲線有交付／生成跳躍時，不應僅用直線連CSV。"""
    return [dict(after_bundle=query, node=node, time=t,
                 occupancy=occupancy(background, node, t), capacity=limit)
            for node, limit in case['buffers'].items()
            for t in breakpoints(background, case['horizon'])]


def stop(output, reason, evidence):
    write_json(output/'failure.json', dict(reason=reason, **evidence))
    write_json(output/'status.json', dict(status='STOP', reason=reason,
                                         performance_comparison_allowed=False))
    raise RuntimeError(f'{reason}: failure.json 已保留；未修改演算法')


def build_statistics(records):
    """無路徑不是零秒誤差；分開呈現可行性一致與成功包抵達誤差。"""
    checks, delays = [], []
    for r in records:
        arrival, expected = r['arrival'], r['independent']['arrival']
        error = None if arrival is None else F(arrival)-F(expected)
        checks.append(dict(bundle=r['bundle']['id'],
            feasibility_matches=(arrival is None)==(expected is None),
            arrival_error_s=error,
            arrival_error_pct=None if expected in (None, 0, '0')
            else F(100)*error/F(expected)))
        if arrival is not None:
            delays.append(float(F(arrival)-F(r['bundle']['g'])))
    return dict(bundles=len(records), accepted=len(delays),
                per_bundle_reference_check=checks,
                delivery_delay_s=dict(mean=statistics.mean(delays), minimum=min(delays),
                                     maximum=max(delays), population_std=statistics.pstdev(delays))
                if delays else None,
                scope='Delay statistics include accepted bundles only; no physical ideal claimed')


def run(case, output, reference_solver=solve):
    validate_case(case)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'input.json', case)
    write_json(output/'status.json', dict(status='RUNNING'))
    quota = {c['id']: c['quota'] for c in case['contacts']}
    background, calendar = deepcopy(case['background']), {}
    contacts = {c['id']: c for c in case['contacts']}
    records, schedule, summaries, label_rows, candidates = [], [], [], [], []
    buffers = buffer_rows(case, background, 'INITIAL')
    try:
        for index, b in enumerate(case['bundles'], 1):
            before = deepcopy((quota, background, calendar))
            actual = search(case, b, quota, background, calendar)
            check = (evaluate(case, b, quota, background, calendar, actual['hops'])
                     if actual['arrival'] is not None else None)
            expected = reference_solver(case, b, quota, background, calendar)
            evidence = dict(case=case, bundle=b, quota=quota, background=background,
                            calendar=calendar, actual=actual, independent=expected,
                            full_schedule_check=check)
            if before != (quota, background, calendar):
                stop(output, 'SEARCH_MUTATED_RESERVATIONS', evidence)
            if check and (not check['feasible'] or check['arrival'] != actual['arrival']):
                stop(output, 'FULL_SCHEDULE_MISMATCH', evidence)
            if actual['arrival'] != expected['arrival']:
                stop(output, 'EARLIEST_ARRIVAL_MISMATCH', evidence)
            before_quota = deepcopy(quota)
            if actual['arrival'] is not None:
                q_new, o_new = commit(case, quota, background, b, actual['hops'])
                q_ref, o_ref = commit_independently(case, b, quota, background, actual['hops'])
                points = sorted(set(breakpoints(o_new, case['horizon'])) |
                                set(breakpoints(o_ref, case['horizon'])))
                if q_new != q_ref or any(occupancy(o_new, v, t) != background_at(o_ref, v, t)
                                       for v in case['buffers'] for t in points):
                    stop(output, 'RESERVATION_MISMATCH', evidence)
                if any(occupancy(o_new, v, t) > case['buffers'][v]
                       for v in case['buffers'] for t in points):
                    stop(output, 'COMMITTED_BUFFER_OVERFLOW', evidence)
                # 完整路徑核對通過後才一次提交三種預約。
                new_calendar = deepcopy(calendar)
                for hop, (cid, s) in enumerate(actual['hops'], 1):
                    c = contacts[cid]
                    f = s + b['size']/c['rate']
                    new_calendar.setdefault(cid, []).append(dict(
                        bundle=b['id'], start=s, finish=f))
                    schedule.append(dict(bundle=b['id'], hop=hop, contact=cid,
                                         sender=c['u'], receiver=c['v'], start=s, finish=f,
                                         receive_start=s+c['delay'], arrival=f+c['delay'],
                                         size=b['size']))
                quota, background, calendar = q_new, o_new, new_calendar
            status = 'ACCEPTED' if actual['arrival'] is not None else 'NO_ROUTE_ON_GRID'
            record = dict(index=index, bundle=b, status=status, **actual,
                          independent=expected, full_schedule_check=check,
                          quota_before=before_quota, quota_after=deepcopy(quota))
            records.append(record)
            write_json(output/f'query_{index:02d}.json', record)
            # 保存每包搜尋前／後狀態，讓失敗原因可重現。
            write_json(output/f'reservations_after_{index:02d}.json', dict(
                quota=quota, background=background, calendar=calendar))
            summaries.append(dict(index=index, bundle=b['id'], source=b['source'],
                                  destination=b['dest'], release=b['g'], size=b['size'],
                                  status=status, arrival=actual['arrival'],
                                  delivery_delay=(actual['arrival']-b['g'])
                                  if actual['arrival'] is not None else None,
                                  path=' → '.join([b['source']] +
                                      [contacts[cid]['v'] for cid, _ in actual['hops']]),
                                  contacts=' → '.join(cid for cid, _ in actual['hops']),
                                  labels_created=actual['labels_created'],
                                  labels_expanded=actual['labels_expanded'],
                                  reference_schedules=expected['schedules_considered'],
                                  reference_arrival=expected['arrival']))
            label_rows.extend(dict(bundle=b['id'], id=lid, **label)
                              for lid, label in actual['labels'].items())
            candidates.extend(dict(bundle=b['id'], **event)
                              for event in actual['trace'] if event['event']=='CANDIDATE')
            buffers.extend(buffer_rows(case, background, b['id']))
        data = dict(name=case['name'], model='PPT_walk_grid_calendar_validation',
                    dominance=False, physical_simulation=False,
                    reference_method=reference_solver.__name__,
                    same_contact_one_bundle_at_a_time=True,
                    records=records, quota=quota, background=background, calendar=calendar)
        write_json(output/'results.json', data)
        write_csv(output/'summary.csv', list(summaries[0]), summaries)
        write_csv(output/'schedule.csv', ['bundle','hop','contact','sender','receiver',
                  'start','finish','receive_start','arrival','size'], schedule)
        write_csv(output/'labels.csv', ['bundle','id','c','A','s','pred'], label_rows)
        write_csv(output/'buffer_breakpoints.csv', ['after_bundle','node','time','occupancy','capacity'], buffers)
        fields = ['bundle','event','label','contact','s','f','h','A','receiver_peak',
                  'receiver_peak_time','sender_peak','sender_peak_time','reason',
                  'new_label','priority','queue_size']
        write_csv(output/'candidates.csv', fields, candidates)
        write_json(output/'statistics.json', build_statistics(records))
        make_report(case, output, data, summaries)
        write_json(output/'status.json', dict(status='VALIDATED_SMALL_CASE',
                    earliest_arrival_matches_exhaustive=True, dominance=False,
                    general_correctness_proven=False, performance_comparison_run=False))
        return data
    except Exception as error:
        current = json.loads((output/'status.json').read_text(encoding='utf-8'))
        if current['status'] != 'STOP':
            write_json(output/'status.json', dict(status='INCOMPLETE_OR_ERROR',
                                                 error=str(error), performance_comparison_run=False))
        raise


def make_report(case, output, data, summaries):
    lines = [f'# {case["name"]}：小案例驗證', '',
             '本輪依新版PPT做有限格點搜尋，保留所有Label，不做支配刪除。',
             '允許節點與contact重訪，以小案例核對，不代表真實衛星模擬、一般證明或效能比較。', '',
             '| Bundle | 路徑 | Contact序列 | 完整抵達秒 | 完整列舉抵達秒 | 結果 |',
             '| --- | --- | --- | ---: | ---: | --- |']
    for row in summaries:
        lines.append(f'| {row["bundle"]} | {row["path"]} | {row["contacts"]} | '
                     f'{row["arrival"]} | {row["reference_arrival"]} | {row["status"]} |')
    lines += ['', '## 判斷與限制', '',
              '- contact容量使用 本路徑已用量＋S≤R[c]，已用量沿pred計算。',
              '- 逐格試起送時間，整包在contact結束前送完，完整抵達不超過horizon。',
              '- 接收端以已接受前包占用＋逐byte接收量檢查整段接收期間。',
              '- 傳送端檢查完整抵達後的等待與逐byte發送釋放。',
              '- 同一contact的已接受發送區間不得重疊，端點可首尾相接。',
              '- 目的地在完整接收後立即交付，交付前峰值仍檢查。',
              '- 依bundles檔案固定順序，成功後才提交容量、Buffer及發送時段。',
              '- 尚未輪到規劃的bundle不預先加入Buffer占用；失敗包不增加預約。',
              '- 不檢查不同contacts共用天線或收發器的互斥，不能外推為硬體排程可執行。',
              '- Label數量與列舉數僅供診斷，本輪沒有比較執行速度。',
              '- horizon目前同時作搜尋／抵達期限，沒有另加每包deadline。',
              '- 四欄Label獨立編號，未加入U或route_usage，也沒有支配規則。', '',
              '## 可檢查的檔案', '',
              '- summary.csv：每包路徑、抵達時間及完整列舉核對。',
              '- schedule.csv：各跳起送、送完、開始接收與完整抵達。',
              '- candidates.csv：每個嘗試時間的接收／傳送峰值與通過或失敗原因。',
              '- labels.csv、query_*.json：Label前驅、Q的POP／加入事件與完整搜尋紀錄。',
              '- reservations_after_*.json：接受各包後的三種資源預約。',
              '- buffer_breakpoints.csv：各次提交後所有分段線性折點的占用。',
              '- statistics.json：成功包延遲的平均、最大、最小及母體標準差。', '',
              '## 延伸拒絕原因（含同一contact在不同Label的重複嘗試）', '']
    for record in data['records']:
        rejected = Counter(e['reason'] for e in record['trace']
                           if e.get('reason') and e['reason']!='PASS')
        lines.append(f'- {record["bundle"]["id"]}：{dict(rejected)}')
    (output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    case = load_scenario(args.config)
    if case.get('algorithm') not in (None, 'ppt_validation_no_dominance'):
        parser.error('請使用 algorithm=ppt_validation_no_dominance，避免誤用legacy設定')
    result = run(case, args.output)
    for record in result['records']:
        print(record['bundle']['id'], record['status'], 'arrival=', record['arrival'],
              'hops=', record['hops'], 'labels=', record['labels_created'])


if __name__ == '__main__':
    main()
