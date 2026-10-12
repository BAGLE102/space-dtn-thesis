# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
"""Composition, replaceable routing, and later-departure regression checks."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from src.experiments.algorithms import resolve_algorithm
from src.experiments.config import ConfigError, load_scenario
from src.experiments.runner import run_scenario
from src.experiments.report import generate
from src.validation.proposed_v04 import search
from src.validation.validation_cases import make, c, b

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/ppt_modular/experiment.json'


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class ModularRoutingChecks(unittest.TestCase):
    # 確認拆分格式組合後的拓樸與需求仍等於 PPT 案例。
    def test_split_config_matches_original_ppt(self):
        modular = load_scenario(CONFIG)
        original = load_scenario(ROOT / 'configs/walkthrough.json')
        for key in ('contacts', 'buffers', 'bundles', 'delta', 'horizon', 'background'):
            self.assertEqual(modular[key], original[key])

    # 切換演算法入口，確認仍共用驗證、報表與預約流程。
    def test_replace_algorithm_preserves_paths_and_shared_validation(self):
        case = load_scenario(CONFIG)
        original = deepcopy(case)
        with tempfile.TemporaryDirectory() as temp:
            results = []
            for index, algorithm in enumerate((
                    'label_setting_v04', 'label_setting_no_dominance',
                    'src.validation.proposed_v04:search')):
                result = run_scenario(case, Path(temp)/str(index), algorithm=algorithm,
                                      verify_oracle=True)
                self.assertEqual([r['arrival'] for r in result['records']], [8, 12])
                self.assertTrue(all(r['independent_schedule_check']['feasible']
                                    for r in result['records']))
                self.assertEqual(result['algorithm'], algorithm)
                reloaded = load_scenario(Path(temp)/str(index)/'input.json')
                self.assertEqual(reloaded, case)
                report = generate(Path(temp)/str(index), draw=False)
                self.assertTrue((report/'report.md').exists())
                results.append(result)
            self.assertFalse(results[1]['dominance'])
            self.assertEqual(results[0]['records'][1]['hops'], results[1]['records'][1]['hops'])
        self.assertEqual(case, original)

    # 確認可獨立更換需求且拓樸內 CSV 相對路徑正確。
    def test_topology_relative_paths_and_demand_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base/'network').mkdir()
            for name in ('topology.json', 'bundles.json', 'experiment.json'):
                (base/name).write_bytes((CONFIG.parent/name).read_bytes())
            (base/'network/contacts.csv').write_bytes(
                (ROOT/'configs/walkthrough_contacts.csv').read_bytes())
            topology = json.loads((base/'topology.json').read_text())
            topology['contacts_file'] = 'contacts.csv'
            (base/'network/topology.json').write_text(json.dumps(topology))
            manifest = json.loads((base/'experiment.json').read_text())
            manifest['topology_file'] = 'network/topology.json'
            (base/'experiment.json').write_text(json.dumps(manifest))
            demands = json.loads((base/'bundles.json').read_text())
            demands['bundles'].reverse()
            (base/'bundles.json').write_text(json.dumps(demands))
            case = load_scenario(base/'experiment.json')
            self.assertEqual(case['bundles'][0]['id'], 'bundle2')
            self.assertEqual(case['contacts'], load_scenario(CONFIG)['contacts'])
            demands['bundles'][0]['source'] = 'missing'
            (base/'bundles.json').write_text(json.dumps(demands))
            with self.assertRaises(ConfigError):
                load_scenario(base/'experiment.json')

    # 前面起送時間超限時，仍須繼續後面的起送時間。
    def test_failed_early_start_does_not_eliminate_contact(self):
        case = make('later_start', [c('a', 'A', 'D', 0, 4)], [b('A', 'D')],
                    horizon=4, background={'D': [[[0, 2, 4, 4], [2, 3, 4, 0]]]})
        with tempfile.TemporaryDirectory() as temp:
            result = run_scenario(case, Path(temp)/'later', verify_oracle=True)
        record = result['records'][0]
        self.assertEqual(record['hops'], [('a', 2)])
        self.assertEqual(record['arrival'], 3)
        attempts = [e for e in record['trace'] if e['event'] == 'EXTEND']
        self.assertEqual([(e['s'], e['reason']) for e in attempts],
                         [(0, 'BUFFER'), (1, 'BUFFER'), (2, 'PASS'), (3, 'PASS')])

    # 無效演算法名稱應在建立輸出與搜尋前被拒絕。
    def test_invalid_algorithm_rejected_before_creating_output(self):
        case = load_scenario(CONFIG)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'invalid'
            with self.assertRaises(ValueError):
                run_scenario(case, target, algorithm='does_not_exist')
            self.assertFalse(target.exists())
        self.assertIs(resolve_algorithm('src.validation.proposed_v04:search').search, search)
