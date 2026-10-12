# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import unittest
from fractions import Fraction as F
from src.validation.validation_cases import cases
from src.validation.proposed_v04 import dominates,search
from src.validation.exhaustive_oracle import solve,evaluate_schedule


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class DominanceChecks(unittest.TestCase):
    # 驗證用量相同也不能只因早到就支配，還必須能持包等待。
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

    # 檢查被保留 Label 是否仍能涵蓋被支配者的可行後續。
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

    # 各 Contact 的用量必須逐項比較，不能只比總量。
    def test_resource_comparison_not_total_sum(self):
        A=dict(v='B',a=F(1),usage={'a':F(4)})
        B=dict(v='B',a=F(2),usage={'b':F(4)})
        self.assertFalse(dominates(A,B,{}, {'B':F(4)}, F(4)))

    # 檢查剪枝減少入隊數時，最早抵達答案仍一致。
    def test_pruning_reduces_enqueued_labels_and_not_value(self):
        case=cases()[4];q={c['id']:c['quota'] for c in case['contacts']};b=case['bundles'][0]
        off=search(case,b,q,{},False);on=search(case,b,q,{},True)
        self.assertEqual(off['arrival'],on['arrival'])
        self.assertLess(on['stats']['enqueued'],off['stats']['enqueued'])
        self.assertGreater(on['stats']['pruned_new'],0)
