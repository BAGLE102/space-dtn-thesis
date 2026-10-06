import unittest
from fractions import Fraction as F
from src.validation.validation_cases import cases
from src.validation.proposed_v04 import dominates,search
from src.validation.exhaustive_oracle import solve,evaluate_schedule


class DominanceChecks(unittest.TestCase):
    def test_waiting_counterexample_same_usage(self):
        case=cases()[3]
        early=dict(v='B',a=F(2),usage={'a':F(4)})
        late=dict(v='B',a=F(8),usage={'a':F(4)})
        self.assertFalse(dominates(early,late,case['background'],case['buffers'],F(4)))
        q={'a':F(0),'b':F(4)}
        late_bundle=dict(source='B',dest='D',g=F(8),size=F(4))
        early_bundle={**late_bundle,'g':F(2)}
        self.assertTrue(evaluate_schedule(case,late_bundle,q,case['background'],[('b',F(9))])['feasible'])
        self.assertFalse(evaluate_schedule(case,early_bundle,q,case['background'],[('b',F(9))])['feasible'])

    def test_all_enumerated_continuations_preserved(self):
        case=cases()[4]
        early=dict(v='B',a=F(1),usage={'a':F(4)})
        late=dict(v='B',a=F(2),usage={'a':F(4)})
        self.assertTrue(dominates(early,late,{},case['buffers'],F(4)))
        q={'a':F(0),'b':F(4)}
        late_bundle=dict(source='B',dest='D',g=F(2),size=F(4))
        early_bundle={**late_bundle,'g':F(1)}
        successors=solve(case,late_bundle,q,{})['feasible_schedules']
        self.assertGreater(len(successors),0)
        for continuation in successors:
            check=evaluate_schedule(case,early_bundle,q,{},continuation['hops'])
            self.assertTrue(check['feasible']);self.assertEqual(check['arrival'],continuation['arrival'])

    def test_resource_comparison_not_total_sum(self):
        A=dict(v='B',a=F(1),usage={'a':F(4)})
        B=dict(v='B',a=F(2),usage={'b':F(4)})
        self.assertFalse(dominates(A,B,{}, {'B':F(4)}, F(4)))

    def test_pruning_reduces_enqueued_labels_and_not_value(self):
        case=cases()[4];q={c['id']:c['quota'] for c in case['contacts']};b=case['bundles'][0]
        off=search(case,b,q,{},False);on=search(case,b,q,{},True)
        self.assertEqual(off['arrival'],on['arrival'])
        self.assertLess(on['stats']['enqueued'],off['stats']['enqueued'])
        self.assertGreater(on['stats']['pruned_new'],0)
