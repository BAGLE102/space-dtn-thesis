"""對照組可漏解；成功路徑仍必須通過與待測方法相同的完整檢查。"""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import unittest

from src.experiments.config import load_scenario
from src.ppt_validation.baseline_single_label import search as baseline
from src.ppt_validation.search import search as proposed
from src.ppt_validation.reference import evaluate
from src.validation.model import commit

ROOT=Path(__file__).resolve().parents[1]


class SingleLabelBaselineChecks(unittest.TestCase):
    def test_same_first_route_but_early_label_can_miss_second_bundle(self):
        case=load_scenario(ROOT/'configs/ppt_modular/experiment_ppt_validation.json')
        quota={c['id']:c['quota'] for c in case['contacts']};bg={};calendar={}
        b=case['bundles'][0]
        frozen=deepcopy((quota,bg,calendar))
        first=baseline(case,b,quota,bg,calendar)
        self.assertEqual(first['arrival'],8)
        self.assertEqual((quota,bg,calendar),frozen)
        self.assertTrue(evaluate(case,b,quota,bg,calendar,first['hops'])['feasible'])
        quota,bg=commit(case,quota,bg,b,first['hops'])
        edges={c['id']:c for c in case['contacts']}
        for cid,s in first['hops']:
            calendar.setdefault(cid,[]).append(dict(bundle=b['id'],start=s,
                finish=s+b['size']/edges[cid]['rate']))
        b=case['bundles'][1]
        got=baseline(case,b,quota,bg,calendar)
        self.assertIsNone(got['arrival'])
        self.assertTrue(got['no_route_is_not_infeasibility_proof'])
        self.assertEqual(proposed(case,b,quota,bg,calendar)['arrival'],12)

    def test_baseline_limit_does_not_mean_no_route(self):
        case=load_scenario(ROOT/'configs/ppt_modular/experiment_ppt_validation.json')
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_BASELINE_LABEL_LIMIT'):
            baseline(case,case['bundles'][0],{c['id']:c['quota'] for c in case['contacts']},
                     {},{},max_labels=1)


if __name__=='__main__':
    unittest.main()
