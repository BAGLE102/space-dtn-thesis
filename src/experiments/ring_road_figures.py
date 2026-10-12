# 先前實驗繪圖工具：讀取已保存的資料；逾時不畫成零接受率。
"""Static scientific figures from compact RRN measurements, without rerunning routing."""
import argparse
import csv
import sys
from pathlib import Path


# 由彙整表及占用資料繪圖；逾時資料以缺值保留，不補零。
def render(short, day, output):
    try:
        import matplotlib
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path('tmp/validation_plot_dependencies').resolve()))
        import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties, fontManager
    font = Path('C:/Windows/Fonts/kaiu.ttf')
    if font.exists():
        fontManager.addfont(str(font))
        plt.rcParams['font.family'] = [FontProperties(fname=str(font)).get_name(), 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    with (short / 'case_summary.csv').open(encoding='utf-8-sig') as stream:
        rows = {r['case']: r for r in csv.DictReader(stream)}
    full = 'sat_day_n1' in rows
    if full:
        rows = {name.replace('_day_', '_900_'): row for name, row in rows.items()}
    output.mkdir(parents=True, exist_ok=True)

    # 同一張圖保存 PNG 與 SVG，統一文字換行且清除行尾空白。
    def save(fig, name):
        fig.savefig(output / f'{name}.png', dpi=160, bbox_inches='tight')
        with (output / f'{name}.svg').open('w', encoding='utf8', newline='\n') as stream:
            fig.savefig(stream, format='svg', bbox_inches='tight')
        svg = output / f'{name}.svg'
        svg.write_text('\n'.join(line.rstrip() for line in
                       svg.read_text(encoding='utf8').splitlines())+'\n',
                       encoding='utf8', newline='\n')
        plt.close(fig)

    counts = [n for n in (1, 5, 10) if rows[f'sat_900_n{n}']['status'] == 'COMPLETE']
    load = [rows[f'sat_900_n{n}'] for n in counts]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), layout='constrained')
    axes[0, 0].plot(counts, [float(r['search_wall_mean_s']) for r in load], 'o-', color='#2563a6')
    axes[0, 0].set(ylabel='平均搜尋時間（秒／Bundle）', title='計算時間：目前實作，單次量測')
    axes[0, 1].plot(counts, [int(r['labels_created_total']) for r in load], 'o-', label='產生')
    axes[0, 1].plot(counts, [int(r['pruned_new_total']) for r in load], 's--', label='建立後被支配')
    axes[0, 1].set(ylabel='Label 數量', title='高剪枝比例不代表免除建立成本')
    axes[0, 1].legend()
    axes[1, 0].plot(counts, [float(r['delay_mean_s']) for r in load], 'o-', color='#16743b')
    axes[1, 0].set(ylabel='平均送達延遲（秒）', title='僅統計模型接受的 Bundle')
    axes[1, 1].bar([str(n) for n in counts], [int(r['contact_overlap_count']) for r in load], color='#b92d2b')
    axes[1, 1].set(ylabel='重疊的傳送區間對數', title='同 Contact 重疊：物理限制診斷')
    for ax in axes.flat:
        ax.set_xlabel('Bundle 數量')
        ax.set_ylim(bottom=0)
        ax.grid(axis='y', alpha=.2)
    span = '完整一天（3,172 條 Contact）' if full else '前 900 秒'
    fig.suptitle(f'Ring Road {span}：衛星 36 → Hot spot 6 的共用資源壓力案例\n'
                 '300 KB／包、Buffer 30 MB、速率 12,500 Bytes/s；非一般隨機流量', fontsize=15)
    save(fig, 'ring_road_load_and_search')

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), layout='constrained')
    size_keys = ['sat_900_n5', 'sat_900_size600_n5', 'sat_900_size1200_n5']
    buffer_keys = ['sat_900_buffer300_n5', 'sat_900_buffer600_n5', 'sat_900_n5']
    for ax, keys, labels, xlabel in (
            (axes[0], size_keys, ['300', '600', '1200'], 'Bundle 大小（KB）'),
            (axes[1], buffer_keys, ['0.3', '0.6', '30'], '各節點 Buffer（MB）')):
        values = [float(rows[k]['acceptance_ratio'])*100
                  if rows[k]['status'] == 'COMPLETE' else float('nan') for k in keys]
        bars = ax.bar(labels, values, color='#2563a6', width=.55)
        ax.set_xticks(range(len(labels)), labels)
        ax.set_xlim(-.6, len(labels)-.4)
        ax.bar_label(bars, labels=[f'{rows[k]["accepted"]}/5'
                     if rows[k]['status']=='COMPLETE' else '' for k in keys], padding=4)
        for index, key in enumerate(keys):
            if rows[key]['status'] != 'COMPLETE':
                ax.text(index, 50, '逾時\n未估計', ha='center', color='#b92d2b')
        ax.set(ylim=(0, 120), ylabel='模型接受比例（%）', xlabel=xlabel)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.grid(axis='y', alpha=.2)
    axes[0].set_title('固定 Buffer 30 MB')
    axes[1].set_title('固定 Bundle 300 KB；來源 Buffer 亦受限')
    fig.suptitle('容量與 Buffer 敏感度：同一來源、目的地、生成時間，共 5 包\n'
                 'Aggregate quota 接受 ≠ 實體鏈路可執行；包含同 Contact 重疊', fontsize=15)
    save(fig, 'ring_road_capacity_and_buffer')

    cold_name = 'cold_day_n5' if full else 'cold_1800_n5'
    profiles = [(cold_name, '中繼 Buffer 30 MB'),
                ('cold_transit_buffer300_n5', '僅中繼 37 Buffer 0.3 MB'),
                ('cold_transit_buffer600_n5', '僅中繼 37 Buffer 0.6 MB')]
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True, layout='constrained')
    found = False
    for ax, (case, label) in zip(axes, profiles):
        path = short / case / 'buffer_samples.csv'
        if not path.exists():
            ax.text(.5, .5, '未完成／未保存曲線', transform=ax.transAxes, ha='center')
            continue
        with path.open(encoding='utf-8-sig') as stream:
            samples = [r for r in csv.DictReader(stream) if r['node'] == '37']
        from fractions import Fraction
        points = [(float(Fraction(r['time'])), float(Fraction(r['occupancy']))) for r in samples]
        found = True
        ax.plot([p[0] for p in points], [p[1] for p in points], color='#d97706')
        limit = float(Fraction(samples[0]['limit']))
        # A 30MB limit is stated in the title; use a readable scale for actual occupancy.
        if limit <= 2:
            ax.axhline(limit, color='#b92d2b', linestyle='--', label=f'上限 {limit} MB')
            ax.legend(loc='upper left')
        ax.set(title=label, ylabel='占用量（MB）', xlim=(0, 1800), ylim=(0, max(1.65, limit*1.1) if limit <= 2 else 1.65))
        ax.grid(alpha=.2)
    axes[-1].set_xlabel('時間（秒）；僅顯示 0–1,800 秒')
    fig.suptitle('冷點 22 → 衛星 37 → Hot spot 5：已接受路徑的 Buffer 回放\n'
                 '來源與其他節點仍為 30 MB；同 Contact 重疊另行記錄', fontsize=15)
    if found:
        save(fig, 'ring_road_transit_buffer')
    else:
        plt.close(fig)

    with (day / 'case_summary.csv').open(encoding='utf-8-sig') as stream:
        timeouts = [r for r in csv.DictReader(stream) if r['status'] == 'TIMEOUT']
    fig, ax = plt.subplots(figsize=(11, 6), layout='constrained')
    ax.barh([r['case'] for r in timeouts], [float(r['wall_s']) for r in timeouts], color='#d97706')
    ax.axvline(20, color='#666', linestyle='--', label='每案例 20 秒上限（含程序啟動／檔案輸出）')
    ax.set(xlabel='程序執行時間（秒）', title='完整一天、3,172 條 Contact：第一筆查詢皆未於上限內完成')
    ax.legend(loc='lower right')
    ax.text(.5, -.13, '逾時不是無路徑；沒有計算出一天的送達率或平均抵達時間。',
            transform=ax.transAxes, ha='center', color='#b92d2b')
    save(fig, 'ring_road_day_timeouts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--short', type=Path, required=True)
    parser.add_argument('--day', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    render(args.short, args.day, args.output)
