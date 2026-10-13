"""批次驗證狀態：超時與截斷檔案不能算成無解或整組完成。"""
import json
from pathlib import Path
import tempfile
import unittest

from src.ppt_validation.ring_road_batch import build_specs, summarize


class BatchValidationStates(unittest.TestCase):
    def test_timeout_counts_only_readable_queries(self):
        spec=build_specs()[0]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'run').mkdir()
            (root/'run/status.json').write_text(json.dumps({'status':'RUNNING'}))
            (root/'run/query_01.json').write_text(json.dumps({'arrival':'1344'}))
            (root/'run/query_02.json').write_text('{')
            row=summarize(root,spec,124)
        self.assertEqual(row['status'],'INCOMPLETE_TIMEOUT')
        self.assertEqual(row['completed_queries'],1)
        self.assertEqual(row['accepted'],1)
        self.assertEqual(row['no_route'],0)
        self.assertEqual(row['unprocessed'],9)
        self.assertEqual(row['unreadable_partial_files'],'query_02.json')

    def test_protocol_declares_buffer_sensitivity(self):
        specs=build_specs()
        self.assertEqual(len(specs),14)
        self.assertEqual(sum(len(s['bundles']) for s in specs),330)
        changed=[s for s in specs if s['buffer_MB']!='30']
        self.assertEqual([s['family'] for s in changed],['buffer_sensitivity'])


if __name__=='__main__':
    unittest.main()
