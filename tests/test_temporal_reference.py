"""確認時間順序完整列舉與原笛卡兒積列舉給出相同答案。"""
from pathlib import Path
import unittest

from src.experiments.config import load_scenario
from src.ppt_validation.reference import solve
from src.ppt_validation.temporal_reference import solve_temporal

ROOT=Path(__file__).resolve().parents[1]


class TemporalReferenceChecks(unittest.TestCase):
    def test_matches_cartesian_reference_with_cycle_and_capacity_failure(self):
        for name in ['repeated_contact','repeated_contact_insufficient']:
            case=load_scenario(ROOT/f'configs/ppt_cycles/{name}.json')
            quota={c['id']:c['quota'] for c in case['contacts']}
            b=case['bundles'][0]
            old=solve(case,b,quota,case['background'],{})
            new=solve_temporal(case,b,quota,case['background'],{})
            self.assertEqual(old['arrival'],new['arrival'])
            self.assertEqual(old['feasible_schedules'],new['feasible_schedules'])

    def test_limit_is_incomplete(self):
        case=load_scenario(ROOT/'configs/ppt_cycles/repeated_contact.json')
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_TEMPORAL_REFERENCE_LIMIT'):
            solve_temporal(case,case['bundles'][0],{},case['background'],{},max_prefixes=1)


if __name__=='__main__':
    unittest.main()
