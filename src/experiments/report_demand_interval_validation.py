"""從隔離實驗原始 CSV 重建比較表、圖與查詢稽核 trace。"""
import argparse
import csv
import json
from pathlib import Path

from src.experiments.demand_interval_validation import Engine, STRATEGIES, make_workload, string_intervals


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directories', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, default=Path('output/demand_interval_validation_20261021/comparison'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    comparisons = []
    all_data = []
    for folder in args.directories:
        meta = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
        rows = read_rows(folder / 'summary.csv')
        all_data.append((meta, rows))
        for scenario in dict.fromkeys(r['scenario'] for r in rows):
            by_strategy = {r['strategy']: r for r in rows if r['scenario'] == scenario}
            lazy = by_strategy['lazy_incremental']
            eager = by_strategy['eager_incremental']
            rebuild = by_strategy['eager_rebuild']
            comparisons.append(dict(contacts=meta['contacts'], scenario=scenario,
                eager_rebuild_median_ms=float(rebuild['ms_median']),
                eager_incremental_median_ms=float(eager['ms_median']),
                lazy_incremental_median_ms=float(lazy['ms_median']),
                speedup_vs_eager_incremental=float(eager['ms_median']) / float(lazy['ms_median']),
                saved_percent_vs_eager_incremental=100 * (1 - float(lazy['ms_median']) / float(eager['ms_median'])),
                eager_solves=int(eager['solves']), lazy_solves=int(lazy['solves']),
                eager_peak_python_bytes=int(eager['peak_python_bytes']), lazy_peak_python_bytes=int(lazy['peak_python_bytes'])))
    with (args.output / 'comparison.csv').open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    lines = ['# 按需元件 pilot：量測摘要', '',
             '數字由原始 CSV 生成。每格時間是所有快照合計的中位數，不是每包路由時間。', '',
             '| Contacts | 情境 | 全重建 ms | 增量全量 ms | 按需增量 ms | 對增量全量加速比 | 重算次數（增量全量→按需） |',
             '|---|---|---:|---:|---:|---:|---|']
    for r in comparisons:
        lines.append(f"| {r['contacts']} | {r['scenario']} | {r['eager_rebuild_median_ms']:.3f} | "
                     f"{r['eager_incremental_median_ms']:.3f} | {r['lazy_incremental_median_ms']:.3f} | "
                     f"{r['speedup_vs_eager_incremental']:.3f}× | {r['eager_solves']}→{r['lazy_solves']} |")
    lines += ['', '加速比小於 1 表示按需較慢；這些受控 query trace 不是完整搜尋或論文重現。',
              '不得據此宣稱交付率、最優性或真實規模加速。完整平均、極值與標準差見各資料夾 summary.csv。']
    (args.output / 'measured_summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    # 輸出一個完整的讀取歷程，顯示 cache 是如何重算／命中的。
    first = all_data[0][0]
    stream = make_workload(1021, first['contacts'], first['epochs'], .1, .02)
    audit = []
    for strategy in STRATEGIES:
        engine = Engine(strategy)
        for epoch, (state, size, deadline, queries) in enumerate(stream[:2]):
            before = engine.solves
            engine.begin(state, size, deadline)
            audit.append(dict(strategy=strategy, epoch=epoch, phase='prepare', contact='',
                              action=f'computed {engine.solves-before} contacts', size=str(size),
                              versions='', intervals=''))
            for cid in queries:
                c = state.contacts[cid]
                before = engine.solves
                result = engine.query(state, cid, size, deadline)
                audit.append(dict(strategy=strategy, epoch=epoch, phase='query', contact=cid,
                                  action='solve' if engine.solves > before else 'cache_hit', size=str(size),
                                  versions=str((state.contact_versions[cid], state.node_versions[c.u], state.node_versions[c.v])),
                                  intervals=json.dumps(string_intervals(result))))
    with (args.output / 'query_trace.csv').open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(all_data), 1, figsize=(12, 4.5 * len(all_data)), squeeze=False)
    colors = ('#aaaaaa', '#75aadb', '#f3a04d', '#28734b')
    for ax, (meta, rows) in zip(axes[:, 0], all_data):
        scenarios = list(dict.fromkeys(r['scenario'] for r in rows))
        for j, (strategy, color) in enumerate(zip(STRATEGIES, colors)):
            selected = [next(r for r in rows if r['scenario'] == s and r['strategy'] == strategy) for s in scenarios]
            ax.bar([i + (j - 1.5) * .19 for i in range(len(scenarios))],
                   [float(r['ms_median']) for r in selected], width=.18, label=strategy, color=color)
        ax.set_xticks(range(len(scenarios)), [s.replace('_', '\n') for s in scenarios], fontsize=9)
        ax.set_yscale('log')
        ax.set_ylabel('Median total time (ms, log scale)')
        ax.set_title(f"Component benchmark: {meta['contacts']} contacts, {meta['epochs']} snapshots, {meta['repeats']} timing repeats")
        ax.grid(axis='y', alpha=.2)
        ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(args.output / 'component_timings.png', dpi=160)
    fig.savefig(args.output / 'component_timings.svg')
    plt.close(fig)
    print(json.dumps(comparisons, indent=2))


if __name__ == '__main__':
    main()
