# 回歸測試：以下中文註解說明每個測試要避免的錯誤情況。
import json
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

from src.experiments.config import load_scenario
from src.experiments.runner import run_scenario
from src.experiments.report import analyze, generate
from src.validation.validation_cases import make, c, b


ROOT=Path(__file__).resolve().parents[1]


# 這組測試驗證指定模組的輸入、結果或邊界；每個案例各自建立隔離狀態。
class ReplayChecks(unittest.TestCase):
    # 核對 PPT 路徑、Buffer 峰值與目的地即交付。
    def test_ppt_routes_buffer_peaks_and_immediate_delivery(self):
        case=load_scenario(ROOT/'configs/walkthrough.json')
        with tempfile.TemporaryDirectory() as temp:
            result=run_scenario(case,Path(temp)/'run',verify_oracle=True)
            replay=analyze(case,result)
            self.assertEqual([route['node_path'] for route in replay['routes']],
                             ['X → B → D','A → B → D'])
            self.assertEqual([route['arrival'] for route in replay['routes']],[8,12])
            self.assertEqual({row['node']:row['peak'] for row in replay['buffer_peaks']},
                             {'X':4,'A':4,'B':4,'C':0,'D':4})
            self.assertEqual(replay['link_conflicts'],[])
            self.assertEqual([event['event'] for event in replay['events']
                              if event['bundle']=='bundle1' and event['time']==8],
                             ['RECEIVE_FINISH','DELIVERED'])
            at_delivery={row['side']:row['occupancy'] for row in replay['buffer_samples']
                         if row['node']=='D' and row['time']==12}
            self.assertEqual(at_delivery,{'left':4,'event_peak':4,'right':0})
            report=generate(Path(temp)/'run',draw=False)
            self.assertTrue((report/'routes.csv').exists())
            self.assertTrue((report/'events.csv').exists())

    # 確認事件之間的占用按分段線性計算。
    def test_exact_linear_inventory_between_events(self):
        case=load_scenario(ROOT/'configs/walkthrough.json')
        with tempfile.TemporaryDirectory() as temp:
            result=run_scenario(case,Path(temp)/'run')
            replay=analyze(case,result)
            # At t=2 B is empty; at t=3 it has all 4MB. Their midpoint is 2MB.
            lines=replay['plot_values']['B']['bundle1']
            at2=[y for t,y in lines if t==2]
            at3=[y for t,y in lines if t==3]
            self.assertEqual((at2[-1]+at3[0])/2,F(2))
            self.assertEqual(replay['final_quota']['c4'],4)

    # 重疊只作診斷，不在報表階段偷偷更改排程。
    def test_contact_overlap_is_diagnostic_not_silently_repaired(self):
        case=make('overlap',[c('one','A','D',0,4,rate=1,quota=4)],
                  [b('A','D',size=2,name='first'),b('A','D',size=2,name='second')],horizon=4)
        with tempfile.TemporaryDirectory() as temp:
            result=run_scenario(case,Path(temp)/'run',verify_oracle=True)
            replay=analyze(case,result)
            self.assertEqual([route['arrival'] for route in replay['routes']],[2,2])
            self.assertEqual(len(replay['link_conflicts']),1)
            conflict=replay['link_conflicts'][0]
            self.assertEqual((conflict['overlap_start'],conflict['overlap_end']),(0,2))

    # 人為改壞路徑，確認完整檢查拒絕且保留證據。
    def test_modified_route_is_rejected_and_preserved(self):
        case=load_scenario(ROOT/'configs/walkthrough.json')
        with tempfile.TemporaryDirectory() as temp:
            run=Path(temp)/'run'
            run_scenario(case,run)
            path=run/'results.json'
            result=json.loads(path.read_text(encoding='utf8'))
            result['records'][0]['hops'][0][1]='0'
            path.write_text(json.dumps(result),encoding='utf8')
            with self.assertRaises(ValueError):
                generate(run,draw=False)
            self.assertTrue((run/'report/failure.json').exists())
