"""檢查網站匯出不洩漏路徑且保留搜尋與資源的時間順序。"""
import json
import unittest
from pathlib import Path
from src.experiments.export_website import export_run

ROOT = Path(__file__).resolve().parents[1]


class WebsiteExportTests(unittest.TestCase):
    def test_ppt_sequential_background(self):
        c = export_run(ROOT/'output/experiments/ppt_modular_20261012', 'PPT')
        self.assertEqual(c['records'][0]['background'], {})
        self.assertIn('B', c['records'][1]['background'])
        self.assertEqual(c['records'][1]['quota_before']['c1'], '0')
        self.assertNotIn(str(ROOT), json.dumps(c))
        self.assertEqual(c['records'][1]['hops'], [['c4','7'], ['c5','10']])

    def test_later_start_kept(self):
        c = export_run(ROOT/'output/experiments/ppt_modular_later_start_check_20261012', '人工案例')
        events = [e for e in c['records'][0]['trace'] if e['event']=='EXTEND']
        self.assertEqual([e['reason'] for e in events[:3]], ['BUFFER','BUFFER','PASS'])
        self.assertEqual(c['records'][0]['hops'][0][1], '2')
