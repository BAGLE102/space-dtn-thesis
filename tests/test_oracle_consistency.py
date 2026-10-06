import ast
import unittest
from pathlib import Path
from src.validation.validation_cases import cases,fractional_gap
from src.validation.compare_oracle import compare_one
from src.validation.exhaustive_oracle import solve


class OracleChecks(unittest.TestCase):
    def test_all_fixed_cases(self):
        for case in cases():
            with self.subTest(case=case['name']):
                self.assertTrue(all(r['match'] for r in compare_one(case)))

    def test_oracle_has_only_standard_library_imports(self):
        tree=ast.parse(Path('src/validation/exhaustive_oracle.py').read_text(encoding='utf-8'))
        allowed={'fractions','itertools','collections','copy'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertIn(node.module,allowed)
            if isinstance(node,ast.Import):
                for name in node.names:self.assertIn(name.name,allowed)

    def test_fractional_optimum_witness(self):
        values=[]
        for delta in (1,'1/2'):
            case=fractional_gap(delta);q={c['id']:c['quota'] for c in case['contacts']}
            values.append(solve(case,case['bundles'][0],q,case['background'])['arrival'])
        self.assertEqual(str(values[0]),'4');self.assertEqual(str(values[1]),'7/2')

    def test_cycle_needed_and_repeated_quota(self):
        for index in (11,12):
            case=cases()[index];q={c['id']:c['quota'] for c in case['contacts']}
            result=solve(case,case['bundles'][0],q,case['background'])
            self.assertEqual(result['arrival'],case['expected'][0])
        self.assertEqual([cid for cid,_ in solve(cases()[11],cases()[11]['bundles'][0],
                         {c['id']:c['quota'] for c in cases()[11]['contacts']},cases()[11]['background'])['hops']],['a','b','c'])
