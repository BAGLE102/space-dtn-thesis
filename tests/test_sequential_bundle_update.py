# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import unittest
from copy import deepcopy
from src.validation.validation_cases import walkthrough,cases
from src.validation.proposed_v04 import search
from src.validation.model import commit,occupancy
from src.validation.exhaustive_oracle import commit_independently
from fractions import Fraction as F


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class SequentialChecks(unittest.TestCase):
    # 確認前包預約確實影響下一包可走的路徑。
    def test_previous_bundle_changes_second_route(self):
        case=walkthrough();q={c['id']:c['quota'] for c in case['contacts']}
        b1,b2=case['bundles'];first=search(case,b1,q,{})
        q2,o2=commit(case,q,{},b1,first['hops'])
        clean=search(case,b2,q,{})
        reserved=search(case,b2,q2,o2)
        self.assertEqual((clean['arrival'],reserved['arrival']),(8,12))
        self.assertEqual([c for c,s in clean['hops']],['c3','c2'])
        self.assertEqual([c for c,s in reserved['hops']],['c4','c5'])
        self.assertEqual(occupancy(o2,'B',F(5,2)),2)
        self.assertEqual(occupancy(o2,'B',F(4)),4)
        self.assertEqual(occupancy(o2,'B',F(8)),0)

    # 確認互斥候選搜尋期間不扣全域容量或加入 Buffer 預約。
    def test_search_does_not_mutate_global_resources(self):
        case=walkthrough();q={c['id']:c['quota'] for c in case['contacts']};o={}
        original=deepcopy((q,o));search(case,case['bundles'][0],q,o)
        self.assertEqual((q,o),original)

    # 提交時只能計入最後選定路徑，不能把候選一起加總。
    def test_commit_counts_only_selected_route(self):
        case=walkthrough();q={c['id']:c['quota'] for c in case['contacts']};b=case['bundles'][0]
        result=search(case,b,q,{})
        nq,no=commit(case,q,{},b,result['hops'])
        self.assertEqual(nq['c1'],0);self.assertEqual(nq['c2'],0)
        self.assertEqual(nq['c5'],4)
        self.assertEqual((nq,no),commit_independently(case,b,q,{},result['hops']))
