import unittest
from fractions import Fraction as F
from src.validation.validation_cases import cases,walkthrough,c,b,make
from src.validation.model import peak,commit
from src.validation.proposed_v04 import check_extension,search


class ExtensionChecks(unittest.TestCase):
    def test_window_end_and_propagation(self):
        case=cases()[6];bundle=case['bundles'][0];edge=case['contacts'][0]
        q={'a':F(4)};L={'v':'A','a':F(0),'usage':{}}
        ok,d=check_extension(case,bundle,q,{},L,edge,F(0))
        self.assertTrue(ok);self.assertEqual(d['f'],1);self.assertEqual(d['arrival'],3)
        self.assertFalse(check_extension(case,bundle,q,{},L,edge,F(1))[0])

    def test_continuity_and_store_forward(self):
        case=cases()[0];bundle=case['bundles'][0];edge=case['contacts'][1]
        q={e['id']:e['quota'] for e in case['contacts']}
        self.assertFalse(check_extension(case,bundle,q,{},dict(v='A',a=0,usage={}),edge,F(2))[0])
        self.assertFalse(check_extension(case,bundle,q,{},dict(v='B',a=3,usage={}),edge,F(2))[0])

    def test_receive_and_sender_drain_overflow(self):
        for case in cases()[7:9]:
            q={c['id']:c['quota'] for c in case['contacts']}
            result=search(case,case['bundles'][0],q,case['background'])
            self.assertIsNone(result['arrival'])
            self.assertTrue(any(e.get('reason')=='BUFFER' for e in result['trace']))

    def test_quota_is_cumulative(self):
        case=cases()[0];bundle=case['bundles'][0];edge=case['contacts'][0]
        ok,d=check_extension(case,bundle,{'a':F(4)}, {},dict(v='A',a=0,usage={'a':F(4)}),edge,F(0))
        self.assertFalse(ok);self.assertEqual(d['reason'],'QUOTA')

    def test_mid_interval_peak_not_just_start_end(self):
        # A completed background receive/transmit peak at 1/2 would be missed by integer sampling.
        bg={'B':[[[F(0),F(1,2),F(0),F(2)],[F(1,2),F(1),F(2),F(0)]]]}
        p,t=peak(bg,'B',[[F(0),F(1),F(4),F(4)]])
        self.assertEqual((p,t),(F(6),F(1,2)))

    def test_destination_peak_before_release(self):
        case=cases()[13];q={c['id']:c['quota'] for c in case['contacts']}
        self.assertIsNone(search(case,case['bundles'][0],q,case['background'])['arrival'])

    def test_reject_unaligned_input_without_rounding(self):
        case=make('unaligned',[c('a','A','D',0,1,rate=3,quota=3)],[b('A','D',size=2)])
        with self.assertRaises(ValueError):search(case,case['bundles'][0],{'a':F(3)}, {})
