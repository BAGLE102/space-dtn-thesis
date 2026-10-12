# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import csv
import json
import tempfile
import unittest
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from src.experiments.config import load_scenario
from src.experiments.runner import CorrectnessFailure, run_scenario
from src.experiments.__main__ import main


ROOT = Path(__file__).resolve().parents[1]


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class ExperimentRunnerChecks(unittest.TestCase):
    # 核對兩包答案、資源更新及四欄位 Label 的前驅回溯。
    def test_walkthrough_results_and_predecessor_reconstruction(self):
        case = load_scenario(ROOT / 'configs/walkthrough.json')
        original = deepcopy(case)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'run'
            result = run_scenario(case, output, verify_oracle=True)
            self.assertEqual([record['arrival'] for record in result['records']], [8, 12])
            self.assertEqual(result['final_quota']['c4'], 4)
            self.assertEqual(result['final_quota']['c5'], 0)
            for record in result['records']:
                reconstructed = []
                goal = next(label for label in record['labels'].values()
                            if label['node'] == record['bundle']['dest']
                            and label['A'] == record['arrival'] and label['active'])
                while goal['pred'] is not None:
                    reconstructed.append((goal['c'], goal['s']))
                    goal = record['labels'][goal['pred']]
                self.assertEqual(list(reversed(reconstructed)), record['hops'])
            status = json.loads((output/'status.json').read_text(encoding='utf8'))
            self.assertEqual(status['status'], 'COMPLETE')
            self.assertFalse(status['transmission_calendar_checked'])
            with (output/'schedule.csv').open(encoding='utf-8-sig', newline='') as stream:
                self.assertEqual([row['contact'] for row in csv.DictReader(stream)],
                                 ['c1', 'c2', 'c4', 'c5'])
            self.assertIn('digraph', (output/'topology.dot').read_text(encoding='utf8'))
            self.assertTrue((output/'query_0002.json').exists())
            exported_config = json.loads((ROOT/'configs/walkthrough.json').read_text(encoding='utf8'))
            exported_config['contacts_file'] = 'contacts.csv'
            (output/'reimport.json').write_text(json.dumps(exported_config), encoding='utf8')
            self.assertEqual(load_scenario(output/'reimport.json')['contacts'], case['contacts'])
        self.assertEqual(case, original)

    # 確認無路徑的 Bundle 不會影響下一包的可用容量。
    def test_unroutable_bundle_does_not_reserve_capacity(self):
        case = load_scenario(ROOT/'configs/minimal.json')
        case['bundles'] = [dict(id='too_large', source='地面站', dest='目的衛星',
                                g=Fraction(0), size=Fraction(8)), case['bundles'][0]]
        with tempfile.TemporaryDirectory() as temp:
            result = run_scenario(case, Path(temp)/'run', verify_oracle=True)
            self.assertEqual([r['status'] for r in result['records']],
                             ['NO_ROUTE_ON_GRID', 'ACCEPTED'])
            self.assertEqual(result['records'][0]['quota_before'], result['records'][0]['quota_after'])
            self.assertEqual(result['records'][1]['arrival'], Fraction(7, 2))

    # 注入錯誤參考答案，確認先保存差異再停止，不能繼續下一包。
    def test_stops_and_preserves_failure_before_next_bundle(self):
        case = load_scenario(ROOT/'configs/walkthrough.json')
        with tempfile.TemporaryDirectory() as temp, patch(
                'src.experiments.runner.solve', return_value={'arrival': Fraction(99)}) as mocked:
            output = Path(temp)/'run'
            with self.assertRaises(CorrectnessFailure):
                run_scenario(case, output, verify_oracle=True)
            self.assertEqual(mocked.call_count, 1)
            self.assertTrue((output/'failure.json').exists())
            self.assertFalse((output/'query_0002.json').exists())
            status = json.loads((output/'status.json').read_text(encoding='utf8'))
            self.assertEqual(status['status'], 'STOP')
            self.assertFalse(status['performance_comparison_allowed'])

    # 確認新的執行不能覆寫已有結果資料夾。
    def test_existing_results_not_overwritten(self):
        case = load_scenario(ROOT/'configs/minimal.json')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'run'
            path.mkdir()
            (path/'keep.txt').write_text('old', encoding='utf8')
            with self.assertRaises(FileExistsError):
                run_scenario(case, path)
            self.assertEqual((path/'keep.txt').read_text(), 'old')

    # 小案例比較開關 dominance 後的抵達時間。
    def test_dominance_toggle_keeps_answer_on_small_case(self):
        case = load_scenario(ROOT/'configs/walkthrough.json')
        with tempfile.TemporaryDirectory() as temp:
            on = run_scenario(case, Path(temp)/'on')
            off = run_scenario(case, Path(temp)/'off', dominance=False)
            self.assertEqual([r['arrival'] for r in on['records']],
                             [r['arrival'] for r in off['records']])

    # 確認命令列驗證及錯誤設定回傳適當退出碼。
    def test_cli_validation_and_error_exit(self):
        with patch('builtins.print'):
            self.assertEqual(main(['--config', str(ROOT/'configs/minimal.json'),
                                   '--validate-only']), 0)
            self.assertEqual(main(['--config', str(ROOT/'configs/missing.json')]), 2)

    # 確認零跳交付仍依來源與目的地峰值語意處理。
    def test_source_equals_destination_with_no_contacts(self):
        case = load_scenario(ROOT/'configs/minimal.json')
        case['contacts'] = []
        case['bundles'][0]['dest'] = '地面站'
        with tempfile.TemporaryDirectory() as temp:
            result = run_scenario(case, Path(temp)/'local', verify_oracle=True)
            self.assertEqual(result['records'][0]['arrival'], 0)
            self.assertEqual(result['records'][0]['hops'], [])
