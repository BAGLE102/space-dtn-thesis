"""將已驗證的搜尋紀錄匯出為 GitHub Pages 資料；不另行執行或修改演算法。"""
import argparse
import json
from copy import deepcopy
from pathlib import Path


def export_run(folder, title):
    folder = Path(folder)
    case = json.loads((folder / 'input.json').read_text(encoding='utf8'))
    result = json.loads((folder / 'results.json').read_text(encoding='utf8'))
    from .config import load_scenario
    from .report import analyze
    # 匯出前重新做獨立排程檢查，不只相信結果檔的 PASS 字串。
    analyze(load_scenario(folder / 'input.json'), result)
    background = deepcopy(case['background'])
    records = []
    for record in result['records']:
        # 只保留網站所需資料，不帶入本機資料夾、診斷紀錄或私人附件。
        r = {k: record[k] for k in ('bundle', 'status', 'arrival', 'hops', 'labels',
                                   'trace', 'quota_before', 'quota_after')}
        r['background'] = deepcopy(background)
        # 每一查詢開始前的占用由已接受路徑重建；候選路徑不占用全域資源。
        if record['status'] == 'ACCEPTED':
            from fractions import Fraction as F
            from src.validation.model import route_curves, jsonable
            parsed = {'contacts': [{k: (F(v) if k in ('start','end','rate','delay','quota') else v)
                                   for k, v in c.items()} for c in case['contacts']]}
            b = {k: (F(v) if k in ('g','size') else v) for k, v in r['bundle'].items()}
            curves = jsonable(route_curves(parsed, b, [(c,F(s)) for c,s in r['hops']]))
            for node, visits in curves.items():
                background.setdefault(node, []).extend(visits)
        records.append(r)
    return {'title': title, 'name': case['name'], 'contacts': case['contacts'],
            'buffers': case['buffers'], 'delta': case['delta'], 'horizon': case['horizon'],
            'records': records, 'verified': True, 'physical_simulation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    payload = export_run(args.run, args.title)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


if __name__ == '__main__':
    main()
