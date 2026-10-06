import unittest
from copy import deepcopy
from src.validation.validation_cases import walkthrough,cases
from src.validation.proposed_v04 import search
from src.validation.model import commit,occupancy
from src.validation.exhaustive_oracle import commit_independently
from fractions import Fraction as F


class SequentialChecks(unittest.TestCase):
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

    def test_search_does_not_mutate_global_resources(self):
        case=walkthrough();q={c['id']:c['quota'] for c in case['contacts']};o={}
        original=deepcopy((q,o));search(case,case['bundles'][0],q,o)
        self.assertEqual((q,o),original)

    def test_commit_counts_only_selected_route(self):
        case=walkthrough();q={c['id']:c['quota'] for c in case['contacts']};b=case['bundles'][0]
        result=search(case,b,q,{})
        nq,no=commit(case,q,{},b,result['hops'])
        self.assertEqual(nq['c1'],0);self.assertEqual(nq['c2'],0)
        self.assertEqual(nq['c5'],4)
        self.assertEqual((nq,no),commit_independently(case,b,q,{},result['hops']))
