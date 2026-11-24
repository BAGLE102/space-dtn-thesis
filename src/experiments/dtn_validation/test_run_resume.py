"""Regression tests for result completeness; no routing algorithm is changed."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dtn import runio
import run_validation as validation
import run_performance as performance
import run_ring_road as ring


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[3]
        self.base = self.workspace / ".codex-ppt-build" / "resume-regression"
        self.base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=str(self.base))
        self.work = Path(self.temp.name).resolve()
        self.assertEqual(os.path.commonpath([str(self.base.resolve()), str(self.work)]), str(self.base.resolve()))

    def tearDown(self):
        # Verify the resolved target before TemporaryDirectory recursively removes it.
        self.assertEqual(os.path.commonpath([str(self.base.resolve()), str(self.work)]), str(self.base.resolve()))
        self.temp.cleanup()

    def rows(self):
        return [dict(case=1, bundle=i, result="same", replay_ok=True) for i in range(3)]

    def completed(self, rows, known=()):
        with patch.object(validation.topology, "small_case", return_value=(None, [None] * 3)):
            return validation.complete_case(rows, known)

    def test_complete_validation_case(self):
        self.assertTrue(self.completed(self.rows()))

    def test_missing_bundle(self):
        self.assertFalse(self.completed(self.rows()[:1]))

    def test_duplicate_bundle_ids(self):
        self.assertFalse(self.completed([self.rows()[0]] * 3))

    def test_legacy_replay_failure(self):
        rows = self.rows()
        rows[0]["replay_ok"] = False
        self.assertFalse(self.completed(rows))

    def test_legacy_wrong_results(self):
        for kind in ["missed", "extra", "later", "invalid"]:
            rows = self.rows()
            rows[0]["result"] = kind
            self.assertFalse(self.completed(rows), kind)

    def test_known_later_is_opt_in(self):
        rows = self.rows()
        rows[0]["result"] = "later"
        self.assertTrue(self.completed(rows, [1]))
        rows[0]["replay_ok"] = False
        self.assertFalse(self.completed(rows, [1]))

    def load(self, path):
        with contextlib.redirect_stdout(io.StringIO()):
            return runio.load_done(str(path), lambda r: r["case"], self.completed)

    def test_complete_line_interruption_not_done(self):
        path = self.work / "interrupted.jsonl"
        path.write_text(json.dumps(self.rows()[0]) + "\n", encoding="utf-8")
        self.assertEqual(self.load(path), set())
        self.assertEqual(path.read_text(), "")

    def test_torn_line_not_done(self):
        path = self.work / "torn.jsonl"
        path.write_text(json.dumps(self.rows()[0]) + '\n{"case":1,"bundle":', encoding="utf-8")
        self.assertEqual(self.load(path), set())

    def test_complete_old_case_kept(self):
        path = self.work / "complete.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in self.rows()), encoding="utf-8")
        self.assertEqual(self.load(path), {1})

    def test_middle_corruption_stops(self):
        path = self.work / "corrupt.jsonl"
        path.write_text('broken\n' + json.dumps(self.rows()[0]) + "\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.load(path)

    def test_failure_separate_from_main_file(self):
        path = self.work / "main.jsonl"
        with self.assertRaises(SystemExit):
            runio.record_failure_and_stop(str(path), self.rows()[0], "injected failure")
        self.assertFalse(path.exists())
        self.assertTrue(Path(runio.failed_path(str(path))).exists())

    def test_performance_group_integrity(self):
        record = dict(N=3, status="complete", rows=[dict(i=i, why="") for i in range(3)])
        self.assertTrue(performance.complete_job([record]))
        for broken in [dict(record, rows=record["rows"][:1]),
                       dict(record, rows=[record["rows"][0]] * 3),
                       dict(record, status="time_limit")]:
            self.assertFalse(performance.complete_job([broken]))
        bad = copy.deepcopy(record)
        bad["rows"][0]["why"] = "VALIDATION_FAILED"
        self.assertFalse(performance.complete_job([bad]))
        self.assertFalse(performance.complete_job([record, record]))

    def test_ring_group_integrity(self):
        record = dict(flows=3, total=3, rows=[dict(i=i, why="") for i in range(3)])
        self.assertTrue(ring.complete_job([record]))
        for broken in [dict(record, rows=record["rows"][:1]),
                       dict(record, rows=[record["rows"][0]] * 3),
                       dict(record, total=1)]:
            self.assertFalse(ring.complete_job([broken]))
        bad = copy.deepcopy(record)
        bad["rows"][0]["why"] = "VALIDATION_FAILED"
        self.assertFalse(ring.complete_job([bad]))

    def test_performance_stops_at_first_failed_bundle(self):
        tc = dict(nodes=2, contacts=1, horizon=10, min_len=1, max_len=2,
                  rates=[1], delays=[0], release=1)
        with patch.object(performance, "plan_one", return_value=(None, "VALIDATION_FAILED")) as plan:
            with self.assertRaises(performance.ScheduleValidationError):
                performance.run_job("test", tc, 1, 3, 3, 1, "ours", None)
            self.assertEqual(plan.call_count, 1)

    def test_ring_stops_at_first_failed_bundle(self):
        from fractions import Fraction
        with patch.object(ring, "plan_one", return_value=(None, "VALIDATION_FAILED")) as plan:
            with self.assertRaises(ring.ScheduleValidationError):
                ring.run_job([], 1, 3, Fraction(3), "ours", False, 10, Fraction(30))
            self.assertEqual(plan.call_count, 1)


if __name__ == "__main__":
    unittest.main()
