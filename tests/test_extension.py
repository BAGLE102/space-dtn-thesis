# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import unittest
from fractions import Fraction as F
from src.validation.validation_cases import cases,walkthrough,c,b,make
from src.validation.model import peak,commit
from src.validation.proposed_v04 import check_extension,search


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class ExtensionChecks(unittest.TestCase):
    # 傳送須在 Contact 結束前完成，傳播後抵達可晚於窗口結束。
    def test_window_end_and_propagation(self):
        case=cases()[6];bundle=case['bundles'][0];edge=case['contacts'][0]
        q={'a':F(4)};L={'v':'A','a':F(0),'usage':{}}
        ok,d=check_extension(case,bundle,q,{},L,edge,F(0))
        self.assertTrue(ok);self.assertEqual(d['f'],1);self.assertEqual(d['arrival'],3)
        self.assertFalse(check_extension(case,bundle,q,{},L,edge,F(1))[0])

    # 確認節點相接且整包完整接收後才能起送。
    def test_continuity_and_store_forward(self):
        case=cases()[0];bundle=case['bundles'][0];edge=case['contacts'][1]
        q={e['id']:e['quota'] for e in case['contacts']}
        self.assertFalse(check_extension(case,bundle,q,{},dict(v='A',a=0,usage={}),edge,F(2))[0])
        self.assertFalse(check_extension(case,bundle,q,{},dict(v='B',a=3,usage={}),edge,F(2))[0])

    # 接收端填入與傳送端逐 byte 釋放都要檢查超限。
    def test_receive_and_sender_drain_overflow(self):
        for case in cases()[7:9]:
            q={c['id']:c['quota'] for c in case['contacts']}
            result=search(case,case['bundles'][0],q,case['background'])
            self.assertIsNone(result['arrival'])
            self.assertTrue(any(e.get('reason')=='BUFFER' for e in result['trace']))

    # 同一路徑重複使用 Contact 時，必須累加該 Contact 用量。
    def test_quota_is_cumulative(self):
        case=cases()[0];bundle=case['bundles'][0];edge=case['contacts'][0]
        ok,d=check_extension(case,bundle,{'a':F(4)}, {},dict(v='A',a=0,usage={'a':F(4)}),edge,F(0))
        self.assertFalse(ok);self.assertEqual(d['reason'],'QUOTA')

    # 確認占用區間中間的折點峰值不會被漏掉。
    def test_mid_interval_peak_not_just_start_end(self):
        # A completed background receive/transmit peak at 1/2 would be missed by integer sampling.
        bg={'B':[[[F(0),F(1,2),F(0),F(2)],[F(1,2),F(1),F(2),F(0)]]]}
        p,t=peak(bg,'B',[[F(0),F(1),F(4),F(4)]])
        self.assertEqual((p,t),(F(6),F(1,2)))

    # 確認目的地交付前仍須容納整包。
    def test_destination_peak_before_release(self):
        case=cases()[13];q={c['id']:c['quota'] for c in case['contacts']}
        self.assertIsNone(search(case,case['bundles'][0],q,case['background'])['arrival'])

    # 未對齊格點的輸入直接拒絕，不偷偷改成另一個問題。
    def test_reject_unaligned_input_without_rounding(self):
        case=make('unaligned',[c('a','A','D',0,1,rate=3,quota=3)],[b('A','D',size=2)])
        with self.assertRaises(ValueError):search(case,case['bundles'][0],{'a':F(3)}, {})
