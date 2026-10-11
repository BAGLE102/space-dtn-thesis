"""Embed saved experiment traces in an offline interactive HTML fragment.

This does not run routing or modify its results. The HTML template is literal
markup in process_view.html; only the JSON data placeholder is substituted.
"""
import argparse
import csv
import json
from pathlib import Path


def load_run(folder, description=None):
    """Read one saved run; shared by the browser view and desktop GUI."""
    folder = Path(folder)
    if (folder/'gui_cancelled.json').exists():
        raise ValueError('This run was cancelled; partial outputs are not a completed experiment.')
    case = json.loads((folder/'input.json').read_text(encoding='utf8'))
    result = json.loads((folder/'results.json').read_text(encoding='utf8'))
    check = json.loads((folder/'report'/'replay_check.json').read_text(encoding='utf8'))
    for record in result['records']:
        ids = set(record['labels'])
        for label in record['labels'].values():
            if label['pred'] is not None and label['pred'] not in ids:
                raise ValueError('Missing predecessor record')
        for event in record['trace']:
            for field in ('queue_before', 'queue_after'):
                if any(label not in ids for label in event.get(field, [])):
                    raise ValueError('Queue references a missing label')
    with (folder/'schedule.csv').open(encoding='utf-8-sig', newline='') as stream:
        schedules = list(csv.DictReader(stream))
    records = [{key: record[key] for key in
                ('bundle', 'arrival', 'hops', 'labels', 'trace', 'status')}
               for record in result['records']]
    return dict(name=case['name'], description=description or case['name'],
                contacts=case['contacts'], buffers=case['buffers'],
                horizon=case['horizon'], records=records,
                schedules=schedules, occupancy=result['final_buffer_occupancy'],
                conflicts=check['link_conflicts'], folder=str(folder.resolve()))


def load_suite(suite):
    suite = Path(suite)
    manifest = json.loads((suite/'manifest.json').read_text(encoding='utf8'))
    payload = []
    for entry in manifest['cases']:
        folder = suite/Path(entry['config']).stem
        run = load_run(folder, entry['description'])
        run.pop('folder')  # Do not embed machine-local paths in the inline data.
        payload.append(run)
    return payload


def build_view(suite, output):
    output = Path(output)
    payload = load_suite(suite)
    template = Path(__file__).with_suffix('.html').read_text(encoding='utf8')
    encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    encoded = encoded.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    assert template.count('__DTN_DATA__') == 1
    fragment = template.replace('__DTN_DATA__', encoded)
    if len(fragment.encode('utf8')) >= 1_000_000:
        raise ValueError('Visualization exceeds 1 MB')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    output.write_text(fragment, encoding='utf8', newline='\n')
    return dict(path=str(output), cases=len(payload),
                records=sum(len(c['records']) for c in payload),
                trace_events=sum(len(r['trace']) for c in payload for r in c['records']))


def main():
    parser = argparse.ArgumentParser(description='把已保存實驗紀錄轉為互動過程重播')
    parser.add_argument('--suite', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_view(args.suite, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
