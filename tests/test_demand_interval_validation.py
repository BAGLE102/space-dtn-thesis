"""隔離區間元件的解析邊界與快取失效測試；不驗證完整路由。"""
from dataclasses import replace
from fractions import Fraction as Q
import unittest

from src.experiments.demand_interval_validation import (
    Contact, Engine, correctness, feasible_starts, plain_state,
)


class DemandIntervalTests(unittest.TestCase):
    def setUp(self):
        self.c = Contact(0, 0, 1, Q(1), Q(10), Q(4), Q(0), Q(40))
        self.state = plain_state(self.c)

    def test_analytic_and_independent_fixed_schedule_checks(self):
        evidence = correctness()
        self.assertEqual(len(evidence['analytic']), 9)
        self.assertGreater(evidence['random_fixed_start_checks'], 9000)

    def test_receiver_version_invalidates(self):
        engine = Engine('lazy_incremental')
        engine.query(self.state, 0, Q(4), Q(20))
        occupied = ((Q(0), Q(4)), (Q(20), Q(4)))
        updated = replace(self.state, curves=(self.state.curves[0], occupied), node_versions=(0, 1))
        self.assertEqual(engine.query(updated, 0, Q(4), Q(20)), ())
        self.assertEqual(engine.solves, 2)

    def test_sender_version_invalidates(self):
        engine = Engine('lazy_incremental')
        engine.query(self.state, 0, Q(4), Q(20))
        occupied = ((Q(0), Q(1)), (Q(20), Q(1)))
        updated = replace(self.state, curves=(occupied, self.state.curves[1]), node_versions=(1, 0))
        self.assertEqual(engine.query(updated, 0, Q(4), Q(20)), ())
        self.assertEqual(engine.solves, 2)

    def test_contact_size_and_deadline_invalidate(self):
        engine = Engine('lazy_incremental')
        self.assertEqual(engine.query(self.state, 0, Q(4), Q(20)), ((Q(1), Q(9)),))
        self.assertEqual(engine.query(self.state, 0, Q(2), Q(20)), ((Q(1), Q(19, 2)),))
        self.assertEqual(engine.query(self.state, 0, Q(2), Q(3)), ((Q(1), Q(5, 2)),))
        changed = replace(self.c, quota=Q(1))
        updated = replace(self.state, contacts=(changed,), contact_versions=(1,))
        self.assertEqual(engine.query(updated, 0, Q(2), Q(3)), ())
        self.assertEqual(engine.solves, 4)

    def test_negative_control_missing_version_is_detectably_stale(self):
        # 故意違反資源版本更新契約，證明測例能抓到失效遺漏。
        engine = Engine('lazy_incremental')
        engine.query(self.state, 0, Q(4), Q(20))
        occupied = ((Q(0), Q(4)), (Q(20), Q(4)))
        broken_update = replace(self.state, curves=(self.state.curves[0], occupied))
        cached = engine.query(broken_update, 0, Q(4), Q(20))
        fresh = feasible_starts(self.c, broken_update, Q(4), Q(20))
        self.assertNotEqual(cached, fresh)


if __name__ == '__main__':
    unittest.main()
