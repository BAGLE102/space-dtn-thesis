"""Scenario execution and inspectable outputs; no simulator or routing changes."""
import csv
import json
from copy import deepcopy
from pathlib import Path

from src.validation.model import commit, jsonable, occupancy
from src.validation.proposed_v04 import search
from src.validation.exhaustive_oracle import (
    solve, evaluate_schedule, commit_independently, background_at,
)


class CorrectnessFailure(RuntimeError):
    """A preserved discrepancy; stop immediately without processing later bundles."""


def write_json(path, data):
    Path(path).write_text(json.dumps(jsonable(data), ensure_ascii=False, indent=2)
                          + '\n', encoding='utf-8', newline='\n')


def write_csv(path, fields, rows):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(jsonable(rows))


def label_view(label):
    """Export the presentation's four fields; retain the frozen engine internally."""
    hop = label['hop']
    return dict(id=label['id'], c=hop[0] if hop else None, A=label['a'],
                s=hop[1] if hop else None, pred=label['pred'],
                node=label['v'], is_source_label=hop is None,
                active=label['active'], processed=label['processed'])


def _stop(output, reason, case, bundle, quota, background, result, check):
    write_json(output / 'failure.json', dict(
        reason=reason, case=case, bundle=bundle, quota=quota,
        background=background, proposed=result, independent=check))
    write_json(output / 'status.json', dict(status='STOP', reason=reason,
                                           failed_bundle=bundle['id'],
                                           performance_comparison_allowed=False))
    raise CorrectnessFailure(f'{reason}；已保存 {output / "failure.json"}')


def run_scenario(case, output, dominance=True, verify_oracle=False, algorithm=None):
    """Use a fresh output directory; commit only independently checked routes."""
    # The legacy default preserves existing monkey-patched callers and GUI behavior.
    search_one = search
    algorithm_name = 'label_setting_v04'
    algorithm = algorithm or case.get('algorithm')
    if algorithm is not None:
        from .algorithms import resolve_algorithm
        selected = resolve_algorithm(algorithm)
        search_one, algorithm_name = selected.search, selected.name
        dominance = dominance and not selected.disable_dominance
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'input.json', case)
    write_json(output / 'status.json', dict(status='RUNNING'))
    quota = {edge['id']: edge['quota'] for edge in case['contacts']}
    background = deepcopy(case['background'])
    edges = {edge['id']: edge for edge in case['contacts']}
    records, summaries, schedules, labels = [], [], [], []
    try:
        for index, bundle in enumerate(case['bundles'], 1):
            before_quota, before_background = deepcopy(quota), deepcopy(background)
            proposed = search_one(case, bundle, quota, background, dominance=dominance)
            accepted = proposed['arrival'] is not None
            route_check = (evaluate_schedule(case, bundle, quota, background, proposed['hops'])
                           if accepted else None)
            reference = solve(case, bundle, quota, background) if verify_oracle else None
            if accepted and (not route_check['feasible']
                             or route_check['arrival'] != proposed['arrival']):
                _stop(output, 'INDEPENDENT_SCHEDULE_MISMATCH', case, bundle,
                      quota, background, proposed, route_check)
            if reference is not None and reference['arrival'] != proposed['arrival']:
                _stop(output, 'EXHAUSTIVE_SEARCH_MISMATCH', case, bundle,
                      quota, background, proposed, reference)
            if (quota, background) != (before_quota, before_background):
                _stop(output, 'SEARCH_MUTATED_RESERVATIONS', case, bundle,
                      before_quota, before_background, proposed, (quota, background))
            if accepted:
                new_q, new_o = commit(case, quota, background, bundle, proposed['hops'])
                independent_q, independent_o = commit_independently(
                    case, bundle, quota, background, proposed['hops'])
                points = {t for profiles in new_o.values() for curve in profiles
                          for segment in curve for t in segment[:2]}
                points |= {t for profiles in independent_o.values() for curve in profiles
                           for segment in curve for t in segment[:2]}
                same = new_q == independent_q and all(
                    occupancy(new_o, node, t) == background_at(independent_o, node, t)
                    for node in case['buffers'] for t in points)
                if not same:
                    _stop(output, 'INDEPENDENT_RESERVATION_MISMATCH', case, bundle,
                          quota, background, proposed, dict(
                              proposed=(new_q, new_o), independent=(independent_q, independent_o)))
                quota, background = new_q, new_o
            record = dict(index=index, bundle=bundle,
                          status='ACCEPTED' if accepted else 'NO_ROUTE_ON_GRID',
                          arrival=proposed['arrival'], hops=proposed['hops'],
                          labels={lid: label_view(label) for lid, label in proposed['labels'].items()},
                          trace=proposed['trace'], stats=proposed['stats'],
                          independent_schedule_check=route_check,
                          oracle_checked=verify_oracle,
                          oracle_arrival=reference['arrival'] if reference else None,
                          quota_before=before_quota, quota_after=deepcopy(quota))
            records.append(record)
            write_json(output / f'query_{index:04d}.json', record)
            summaries.append(dict(index=index, bundle=bundle['id'], source=bundle['source'],
                                  destination=bundle['dest'], size=bundle['size'],
                                  release=bundle['g'], status=record['status'],
                                  arrival=proposed['arrival'],
                                  delivery_delay=(proposed['arrival']-bundle['g']) if accepted else None,
                                  hops=len(proposed['hops']),
                                  labels_created=proposed['stats']['created'],
                                  labels_expanded=proposed['stats']['expanded'],
                                  oracle_checked=verify_oracle))
            for hop_index, (cid, start) in enumerate(proposed['hops'], 1):
                edge = edges[cid]
                finish = start + bundle['size'] / edge['rate']
                schedules.append(dict(bundle=bundle['id'], hop=hop_index, contact=cid,
                                      sender=edge['u'], receiver=edge['v'], start=start,
                                      finish=finish, receive_start=start+edge['delay'],
                                      arrival=finish+edge['delay'], size=bundle['size']))
            for label in record['labels'].values():
                labels.append(dict(bundle=bundle['id'], **label))
    except CorrectnessFailure:
        raise
    except Exception as error:
        write_json(output / 'status.json', dict(status='ERROR', error=str(error)))
        raise
    results = dict(name=case['name'], model='frozen_v04_finite_grid_aggregate_capacity',
                   algorithm=algorithm_name,
                   units=dict(time='s', data='MB', rate='MB/s'),
                   dominance=dominance, oracle_checked=verify_oracle,
                   transmission_calendar_checked=False, physical_simulation=False,
                   records=records, final_quota=quota, final_buffer_occupancy=background)
    write_json(output / 'results.json', results)
    write_json(output / 'reservations.json', dict(remaining_capacity=quota,
                                                buffer_occupancy=background))
    write_csv(output / 'summary.csv', [
        'index', 'bundle', 'source', 'destination', 'size', 'release', 'status',
        'arrival', 'delivery_delay', 'hops', 'labels_created', 'labels_expanded',
        'oracle_checked'], summaries)
    write_csv(output / 'schedule.csv', [
        'bundle', 'hop', 'contact', 'sender', 'receiver', 'start', 'finish',
        'receive_start', 'arrival', 'size'], schedules)
    write_csv(output / 'labels.csv', [
        'bundle', 'id', 'c', 'A', 's', 'pred', 'node', 'is_source_label', 'active',
        'processed'], labels)
    departure_rows = []
    for record in records:
        for event in record['trace']:
            if event['event'] != 'EXTEND':
                continue
            departure_rows.append(dict(
                bundle=record['bundle']['id'], parent_label=event['selected'],
                contact=event['contact'], start=event['s'], arrival=event['arrival'],
                reason=event['reason'], candidate_label=event.get('new_label', ''),
                dominated_by=';'.join(event.get('dominated_by', []))))
    write_csv(output / 'departure_candidates.csv', [
        'bundle', 'parent_label', 'contact', 'start', 'arrival', 'reason',
        'candidate_label', 'dominated_by'], departure_rows)
    write_csv(output / 'contacts.csv', [
        'id', 'source', 'target', 'start', 'end', 'rate', 'delay', 'remaining_capacity'],
        [dict(id=edge['id'], source=edge['u'], target=edge['v'], start=edge['start'],
              end=edge['end'], rate=edge['rate'], delay=edge['delay'],
              remaining_capacity=edge['quota']) for edge in case['contacts']])
    write_csv(output / 'nodes.csv', ['id', 'buffer'],
              [dict(id=node, buffer=capacity) for node, capacity in case['buffers'].items()])
    # Graphviz DOT is a portable topology description, not a new diagram layout.
    dot = ['digraph contact_topology {', '  rankdir=LR;']
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    for node, capacity in case['buffers'].items():
        dot.append(f'  {quote(node)} [label={quote(f"{node} / buffer={capacity} MB")}];')
    for edge in case['contacts']:
        label = (f'{edge["id"]} [{edge["start"]},{edge["end"]}) '
                 f'r={edge["rate"]}, delay={edge["delay"]}, R={edge["quota"]}')
        dot.append(f'  {quote(edge["u"])} -> {quote(edge["v"])} [label={quote(label)}];')
    dot.append('}')
    (output / 'topology.dot').write_text('\n'.join(dot)+'\n', encoding='utf-8', newline='\n')
    write_json(output / 'status.json', dict(
        status='COMPLETE', bundles=len(records),
        accepted=sum(record['status'] == 'ACCEPTED' for record in records),
        oracle_checked=verify_oracle, correctness_claim='tested_input_only',
        transmission_calendar_checked=False, performance_comparison_run=False))
    return results
