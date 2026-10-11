"""Importer boundary and instrumentation checks, without requiring downloaded data."""
import json
import tempfile
import unittest
from pathlib import Path

from src.experiments import runner
from src.experiments.config import load_scenario
from src.experiments.ring_road import (
    convert_contacts, worker, destination_lower_bound, read_complete_json_files,
)


class RingRoadExperiments(unittest.TestCase):
    def test_interrupted_json_is_preserved_but_not_counted_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder/'query_0001.json').write_text('{"status":"ACCEPTED"}', encoding='utf8')
            (folder/'query_0002.json').write_text('{"status":', encoding='utf8')
            records, incomplete = read_complete_json_files(folder, 'query_*.json')
            self.assertEqual(records, [{'status': 'ACCEPTED'}])
            self.assertEqual(incomplete, ['query_0002.json'])
            self.assertTrue((folder/'query_0002.json').exists())

    def test_compact_search_preserves_decisions_queue_sizes_and_statistics(self):
        from copy import deepcopy
        from src.experiments.compact_search import search as compact_search
        from src.validation.proposed_v04 import search as literal_search
        from src.validation.model import commit
        keys = ('event', 'selected', 'contact', 'reason', 'new_label', 'dominated_by', 'removed')
        for path in sorted(Path('configs/experiments_v01').glob('*.json')):
            if path.name == 'manifest.json':
                continue
            for dominance in (True, False):
                case = load_scenario(path)
                quota = {edge['id']: edge['quota'] for edge in case['contacts']}
                background = deepcopy(case['background'])
                for bundle in case['bundles']:
                    with self.subTest(case=path.name, dominance=dominance, bundle=bundle['id']):
                        left = literal_search(case, bundle, quota, background, dominance)
                        right = compact_search(case, bundle, quota, background, dominance)
                        counters = compact_search(case, bundle, quota, background,
                                                  dominance, trace_events=False)
                        self.assertEqual(left['arrival'], right['arrival'])
                        self.assertEqual(left['hops'], right['hops'])
                        self.assertEqual(left['stats'], right['stats'])
                        self.assertEqual((right['arrival'], right['hops'], right['stats']),
                                         (counters['arrival'], counters['hops'], counters['stats']))
                        if 'diagnostics' in right:
                            self.assertEqual(right['diagnostics'], counters['diagnostics'])
                        self.assertEqual([{k:e[k] for k in keys if k in e} for e in left['trace']],
                                         [{k:e[k] for k in keys if k in e} for e in right['trace']])
                        self.assertEqual([len(e.get('queue_after', [])) for e in left['trace']],
                                         [e.get('queue_count', 0) for e in right['trace']])
                        if left['arrival'] is not None:
                            quota, background = commit(case, quota, background, bundle, left['hops'])

    def test_last_contact_bound_is_a_relaxation_not_a_route(self):
        from fractions import Fraction as F
        case = load_scenario(Path('configs/walkthrough.json'))
        bundle = case['bundles'][1]
        quota = {c['id']: c['quota'] for c in case['contacts']}
        # c8 gives an optimistic bound, although A cannot reach it in time.
        self.assertEqual(destination_lower_bound(case, bundle, quota), F(3))
        for c in case['contacts']:
            if c['v'] == bundle['dest']:
                quota[c['id']] = 0
        self.assertIsNone(destination_lower_bound(case, bundle, quota))

    def test_import_preserves_direction_identity_and_clips_only_horizon(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'contacts.txt'
            source.write_text('a contact +0 +100 48 1 125000000\n'
                              'a contact +4 +12 7 32 12500\n'
                              'a range +0 +100 7 32 0\n'
                              'a contact +4 +12 32 7 12500\n'
                              'a contact +20 +30 8 33 12500\n', encoding='utf8')
            rows = convert_contacts(source, 10, '1/80')
            self.assertEqual([(r['id'], r['source'], r['target'], r['start'], r['end'])
                              for r in rows], [('rrn_0002', '7', '32', '4', '10'),
                                               ('rrn_0003', '32', '7', '4', '10')])

    def test_measurements_do_not_change_routes_or_leave_search_patched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = Path('configs/walkthrough.json').resolve()
            case = load_scenario(config)
            plain = runner.run_scenario(case, root / 'plain', verify_oracle=True)
            original = runner.search
            worker(config, root / 'measured')
            self.assertIs(runner.search, original)
            measured = json.loads((root / 'measured/results.json').read_text(encoding='utf8'))
            for left, right in zip(plain['records'], measured['records']):
                self.assertEqual(str(left['arrival']), right['arrival'])
                self.assertEqual([(c, str(s)) for c, s in left['hops']],
                                 [tuple(hop) for hop in right['hops']])
                self.assertEqual(left['stats'], right['stats'])
            self.assertTrue((root / 'measured/measure_bundle1.json').exists())
            self.assertTrue((root / 'measured/buffer_peaks.json').exists())


if __name__ == '__main__':
    unittest.main()
