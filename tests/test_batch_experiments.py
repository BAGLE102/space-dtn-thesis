"""Checks for suite completion and fail-fast evidence preservation."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.experiments.batch import run_batch
from src.experiments.runner import CorrectnessFailure

ROOT = Path(__file__).resolve().parents[1]


class BatchExperiments(unittest.TestCase):
    def prepare(self, directory, indices):
        source = ROOT/'configs'/'experiments_v01'
        manifest = json.loads((source/'manifest.json').read_text(encoding='utf8'))
        manifest['cases'] = [manifest['cases'][i] for i in indices]
        for entry in manifest['cases']:
            (directory/entry['config']).write_bytes((source/entry['config']).read_bytes())
        path=directory/'manifest.json'
        path.write_text(json.dumps(manifest),encoding='utf8')
        return path,manifest

    def test_baseline_and_known_boundary_are_distinguished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            manifest,_=self.prepare(root,[0,8])
            with contextlib.redirect_stdout(io.StringIO()):
                run_batch(manifest,root/'run')
            status=json.loads((root/'run'/'status.json').read_text())
            self.assertEqual(status['status'],'COMPLETE')
            self.assertTrue(status['oracle_match'])
            self.assertFalse(status['performance_comparison_run'])
            check=json.loads((root/'run'/'09_aggregate_overlap'/'report'/'replay_check.json').read_text())
            self.assertEqual(len(check['link_conflicts']),1)

    def test_expectation_failure_stops_later_cases_and_keeps_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path,manifest=self.prepare(root,[0,8])
            manifest['cases'][0]['expected_arrivals']=['999','12']
            path.write_text(json.dumps(manifest),encoding='utf8')
            with self.assertRaises(CorrectnessFailure):
                run_batch(path,root/'run')
            self.assertTrue((root/'run'/'01_ppt_baseline'/'expectation_failure.json').exists())
            self.assertFalse((root/'run'/'09_aggregate_overlap').exists())
            status=json.loads((root/'run'/'status.json').read_text())
            self.assertEqual(status['status'],'STOP')
            self.assertFalse(status['performance_comparison_allowed'])


if __name__=='__main__':
    unittest.main()
