# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import json
import tempfile
import unittest
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

from src.experiments.config import ConfigError, load_scenario
from src.validation.validation_cases import walkthrough


ROOT = Path(__file__).resolve().parents[1]


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class ScenarioConfigChecks(unittest.TestCase):
    # 將測試設定寫入臨時檔後走正式載入器，避免繞過輸入驗證。
    def write_case(self, path, raw):
        path.write_text(json.dumps(raw, ensure_ascii=False), encoding='utf-8')
        return load_scenario(path)

    # 確認 CSV 載入後與人工 PPT 案例的 Contact 完全一致。
    def test_csv_scenario_matches_existing_walkthrough(self):
        loaded = load_scenario(ROOT / 'configs/walkthrough.json')
        original = walkthrough()
        for key in ('contacts', 'bundles', 'buffers', 'delta', 'horizon', 'background'):
            self.assertEqual(loaded[key], original[key])

    # 確認中文 ID 與有理數不在載入時失真。
    def test_unicode_nodes_and_exact_fractions(self):
        case = load_scenario(ROOT / 'configs/minimal.json')
        self.assertIn('地面站', case['buffers'])
        self.assertEqual(case['delta'], Fraction(1, 2))
        self.assertEqual(case['contacts'][0]['quota'], 4)

    # 確保舊版保存的案例仍可重新載入。
    def test_legacy_saved_case_is_importable(self):
        case = load_scenario(ROOT / 'output/validation/walkthrough_input.json')
        self.assertEqual(case, walkthrough())

    # 錯誤欄位、數值、單位或格點應在搜尋前被拒絕。
    def test_invalid_fields_fail_before_search(self):
        template = json.loads((ROOT / 'configs/minimal.json').read_text(encoding='utf8'))
        invalid = [
            ('unknown node', lambda d: d['contacts'][0].update(target='unknown')),
            ('duplicate node', lambda d: d['nodes'].append(deepcopy(d['nodes'][0]))),
            ('duplicate contact', lambda d: d['contacts'].append(deepcopy(d['contacts'][0]))),
            ('duplicate bundle', lambda d: d['bundles'].append(deepcopy(d['bundles'][0]))),
            ('negative buffer', lambda d: d['nodes'][0].update(buffer=-1)),
            ('negative release', lambda d: d['bundles'][0].update(release=-1)),
            ('zero rate', lambda d: d['contacts'][0].update(rate=0)),
            ('too much quota', lambda d: d['contacts'][0].update(remaining_capacity=5)),
            ('self loop', lambda d: d['contacts'][0].update(target='地面站')),
            ('unaligned duration', lambda d: d['contacts'][0].update(rate=3)),
            ('typo', lambda d: d['contacts'][0].update(ratee=4)),
            ('boolean buffer', lambda d: d['nodes'][0].update(buffer=True)),
            ('zero time step', lambda d: d.update(time_step=0)),
            ('nan', lambda d: d['contacts'][0].update(rate='NaN')),
            ('both contact sources', lambda d: d.update(contacts_file='x.csv')),
            ('bad units', lambda d: d['units'].update(data='bytes')),
            ('unknown schema', lambda d: d.update(schema_version=2)),
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'case.json'
            for name, mutate in invalid:
                with self.subTest(name=name):
                    raw = deepcopy(template)
                    mutate(raw)
                    with self.assertRaises(ConfigError):
                        self.write_case(path, raw)

    # 確認 CSV 路徑以設定檔位置為基準，不受 shell 工作目錄影響。
    def test_csv_path_is_relative_to_config_not_current_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'walkthrough_contacts.csv').write_bytes(
                (ROOT / 'configs/walkthrough_contacts.csv').read_bytes())
            (directory / 'scenario.json').write_bytes((ROOT / 'configs/walkthrough.json').read_bytes())
            self.assertEqual(load_scenario(directory / 'scenario.json')['contacts'],
                             walkthrough()['contacts'])

    # 確認缺少檔案或 CSV 欄位數錯誤不會默默略過。
    def test_malformed_csv_and_missing_file_are_rejected(self):
        raw = json.loads((ROOT / 'configs/walkthrough.json').read_text(encoding='utf8'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'case.json'
            with self.assertRaises(ConfigError):
                self.write_case(path, raw)
            (Path(temp) / 'walkthrough_contacts.csv').write_text(
                'id,source,target,start,end,rate\nc,A,B,0,1,4,EXTRA\n', encoding='utf8')
            with self.assertRaises(ConfigError):
                self.write_case(path, raw)

    # 確認合法的孤立節點與零 Buffer 不被額外排除。
    def test_isolated_node_and_zero_buffer_allowed(self):
        raw = json.loads((ROOT / 'configs/minimal.json').read_text(encoding='utf8'))
        raw['nodes'].append({'id': 'unused', 'buffer': 0})
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(self.write_case(Path(temp)/'case.json', raw)['buffers']['unused'], 0)

    # 確認長小數先轉字串，不在 JSON 匯入階段四捨五入。
    def test_decimal_literals_are_not_rounded_by_json_parser(self):
        raw = json.loads((ROOT / 'configs/minimal.json').read_text(encoding='utf8'))
        raw['contacts'] = []
        raw['bundles'][0]['destination'] = '地面站'
        raw['time_step'] = 'DECIMAL_LITERAL'
        text = json.dumps(raw, ensure_ascii=False).replace(
            '"DECIMAL_LITERAL"', '0.10000000000000000000000001')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'exact.json'
            path.write_text(text, encoding='utf8')
            self.assertEqual(load_scenario(path)['delta'],
                             Fraction('0.10000000000000000000000001'))

    # 確認歷史格式中的超限或不合法初始曲線會被拒絕。
    def test_legacy_invalid_initial_occupancy_rejected(self):
        raw = json.loads((ROOT / 'output/validation/walkthrough_input.json').read_text(encoding='utf8'))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'case.json'
            for background in ({'missing': [[[0, 1, 1, 1]]]},
                               {'B': [[[0, 1, 5, 5]]]},
                               {'B': [[[0, 2, 1, 1], [1, 3, 1, 1]]]},
                               {'B': [[[1, 1, 0, 4]]]}):
                with self.subTest(background=background):
                    raw['background'] = background
                    with self.assertRaises(ConfigError):
                        self.write_case(path, raw)
