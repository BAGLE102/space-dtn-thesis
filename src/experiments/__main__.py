"""Run: python -m src.experiments --config configs/walkthrough.json"""
import argparse
from datetime import datetime
from pathlib import Path
import sys

from .config import ConfigError, load_scenario
from .runner import CorrectnessFailure, run_scenario


def main(argv=None):
    parser = argparse.ArgumentParser(description='可設定拓樸的 Space DTN v04 實驗入口')
    parser.add_argument('--config', required=True, type=Path, help='JSON案例檔')
    parser.add_argument('--output', type=Path, help='新的輸出資料夾；不覆蓋既有結果')
    parser.add_argument('--oracle', action='store_true', help='啟用小案例完整搜尋比對（可能很慢）')
    parser.add_argument('--no-dominance', action='store_true', help='停用支配剪枝')
    parser.add_argument('--algorithm', help='演算法名稱或本機 module:function；覆蓋設定檔選擇')
    parser.add_argument('--validate-only', action='store_true', help='只檢查設定，不搜尋或輸出')
    args = parser.parse_args(argv)
    try:
        case = load_scenario(args.config)
        algorithm = args.algorithm or case.get('algorithm', 'label_setting_v04')
        from .algorithms import resolve_algorithm
        resolve_algorithm(algorithm)
        if args.validate_only:
            print(f'設定有效：{case["name"]}；{len(case["buffers"])} nodes、'
                  f'{len(case["contacts"])} contacts、{len(case["bundles"])} bundles')
            return 0
        output = args.output or Path('output/experiments') / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        result = run_scenario(case, output, dominance=not args.no_dominance,
                              verify_oracle=args.oracle, algorithm=algorithm)
    except (ValueError, FileExistsError, CorrectnessFailure, OSError) as error:
        print(f'停止：{error}', file=sys.stderr)
        return 2
    print(f'完成：{case["name"]}')
    for record in result['records']:
        route = ' → '.join(cid for cid, _ in record['hops']) or '（無傳輸）'
        print(f'  {record["bundle"]["id"]}: {record["status"]}, '
              f'arrival={record["arrival"]}, route={route}')
    print(f'輸出：{output.resolve()}')
    print('模型：有限格點＋aggregate容量；尚未檢查鏈路傳輸時間衝突。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
