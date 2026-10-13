"""PPT驗證版：針對晚起送、等待衝突、接收中途峰值與Q順序。"""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest

from src.experiments.config import load_scenario
from src.ppt_validation.search import Label, receiver_candidates, search, transmission_free
from src.ppt_validation.reference import evaluate, solve
from src.ppt_validation.run import run
from src.validation.model import normalize

ROOT = Path(__file__).resolve().parents[1]


def simple_case():
    return normalize(dict(name='later_start', delta=1, horizon=4,
        buffers={'A':4,'B':4}, background={},
        contacts=[dict(id='c',u='A',v='B',start=0,end=3,rate=4,delay=0,quota=12)],
        bundles=[dict(id='b',source='A',dest='B',g=0,size=4)]))


class PptValidationChecks(unittest.TestCase):
    def test_busy_early_start_keeps_later_slot_and_boundary(self):
        case = simple_case(); b = case['bundles'][0]
        calendar = {'c':[dict(bundle='prior',start=F(0),finish=F(1))]}
        q = {'c':F(12)}
        frozen = deepcopy((q, case['background'], calendar))
        got = search(case,b,q,case['background'],calendar)
        self.assertEqual(got['hops'], [('c',F(1))])
        self.assertEqual(got['arrival'], 2)
        self.assertEqual(solve(case,b,q,case['background'],calendar)['arrival'],2)
        self.assertEqual(frozen,(q,case['background'],calendar))
        self.assertFalse(evaluate(case,b,q,{},calendar,[('c',F(0))])['feasible'])
        self.assertTrue(transmission_free(calendar,'c',F(1),F(2)))
        self.assertTrue(any(e.get('reason')=='CONTACT_BUSY' for e in got['trace']))

    def test_receiver_interior_breakpoint_is_checked(self):
        case = simple_case(); b=case['bundles'][0]
        # 兩端占用0，中間既有占用4MB；只看接收起訖會錯誤接受s=0。
        case['background']={'B':[[[F(0),F(1,2),F(0),F(4)],
                                   [F(1,2),F(1),F(4),F(0)]]]}
        candidates=list(receiver_candidates(case,b,Label(None,F(0),None,None),
                                            case['contacts'][0],case['background']))
        self.assertEqual(candidates[0]['reason'],'RECEIVER_BUFFER')
        self.assertEqual(candidates[0]['receiver_peak'],6)
        self.assertEqual(candidates[1]['reason'],'RECEIVER_PASS')
        got=search(case,b,{'c':F(12)},case['background'],{})
        self.assertEqual(got['hops'],[('c',F(1))])

    def test_ppt_early_receive_passes_but_waiting_fails(self):
        case=load_scenario(ROOT/'configs/ppt_modular/experiment_ppt_validation.json')
        with tempfile.TemporaryDirectory() as directory:
            got=run(case,Path(directory)/'result')
        self.assertEqual([r['arrival'] for r in got['records']],[8,12])
        second=got['records'][1]
        c3=[e for e in second['trace'] if e.get('contact')=='c3']
        self.assertTrue(any(e.get('reason')=='PASS' for e in c3))
        early=next(e['new_label'] for e in c3 if e.get('reason')=='PASS')
        c5=[e for e in second['trace'] if e.get('label')==early and e.get('contact')=='c5']
        self.assertTrue(any(e.get('reason')=='SENDER_BUFFER' for e in c5))
        self.assertEqual(second['hops'],[('c4',F(7)),('c5',F(10))])
        # 不做dominance，因此c4在7、8兩種開始時間皆保留。
        self.assertEqual(sorted(l['s'] for l in second['labels'].values() if l['c']=='c4'),[7,8])
        popped=[e['A'] for e in second['trace'] if e['event']=='POP']
        self.assertEqual(popped,sorted(popped))

    def test_no_route_and_full_listing_agree(self):
        case=simple_case(); b=case['bundles'][0]
        calendar={'c':[dict(bundle='prior',start=F(0),finish=F(3))]}
        self.assertIsNone(search(case,b,{'c':F(12)},{},calendar)['arrival'])
        self.assertIsNone(solve(case,b,{'c':F(12)},{},calendar)['arrival'])

    def test_cycle_reuses_contact_and_commit_deducts_each_visit(self):
        case=load_scenario(ROOT/'configs/ppt_cycles/repeated_contact.json')
        with tempfile.TemporaryDirectory() as directory:
            result=run(case,Path(directory)/'cycle')
        record=result['records'][0]
        self.assertEqual(record['hops'], [('ab',0),('ba',2),('ab',3),('bd',4)])
        self.assertEqual(record['arrival'],5)
        self.assertEqual(record['independent']['arrival'],5)
        self.assertEqual(result['quota']['ab'],0)
        self.assertEqual([(x['start'],x['finish']) for x in result['calendar']['ab']],[(0,1),(3,4)])
        self.assertTrue(record['full_schedule_check']['feasible'])
        self.assertTrue(all(set(lab)=={'c','A','s','pred'} for lab in record['labels'].values()))

    def test_repeated_contact_requires_accumulated_capacity(self):
        case=load_scenario(ROOT/'configs/ppt_cycles/repeated_contact_insufficient.json')
        b=case['bundles'][0]; quota={c['id']:c['quota'] for c in case['contacts']}
        result=search(case,b,quota,case['background'],{})
        self.assertIsNone(result['arrival'])
        self.assertIsNone(solve(case,b,quota,case['background'],{})['arrival'])
        self.assertTrue(any(e.get('reason')=='CAPACITY' and e.get('used')==1
                            for e in result['trace']))

    def test_finite_horizon_ends_cycle_without_destination(self):
        case=simple_case(); b=case['bundles'][0]
        case['buffers']['D']=F(4); b['dest']='D'; case['horizon']=F(3)
        case['contacts'].append(dict(id='back',u='B',v='A',start=F(1),end=F(3),
                                     rate=F(4),delay=F(0),quota=F(8)))
        quota={c['id']:c['quota'] for c in case['contacts']}
        self.assertIsNone(search(case,b,quota,{}, {})['arrival'])
        reference=solve(case,b,quota,{}, {})
        self.assertIsNone(reference['arrival'])
        self.assertEqual(reference['depth_bound'],3)

    def test_reference_walk_limit_is_not_no_route(self):
        case=load_scenario(ROOT/'configs/ppt_cycles/repeated_contact.json')
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_REFERENCE_WALK_LIMIT'):
            solve(case,case['bundles'][0],{c['id']:c['quota'] for c in case['contacts']},
                  case['background'],{},max_walk_prefixes=1)

    def test_search_limit_is_not_no_route(self):
        case=simple_case(); b=case['bundles'][0]
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_LABEL_LIMIT'):
            search(case,b,{'c':F(12)},{},{},max_labels=1)


if __name__=='__main__':
    unittest.main()
