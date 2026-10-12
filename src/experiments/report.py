# 事後重播與報表：計算既定排程的 Buffer 和 Contact 重疊；不修正搜尋結果。
"""Replay selected schedules and produce route tables and scientific figures.

Uses exact inventory functions for replay; rendering never determines feasibility.
Does not change the frozen router or repair conflicting schedules.
"""
import argparse
import json
import math
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

from .config import load_scenario
from .runner import write_json, write_csv
from src.validation.exhaustive_oracle import (
    evaluate_schedule, commit_independently, background_at, visits_for, inventory,
)


# 依既定排程重建精確占用、峰值與傳送重疊；不是重新尋找可行路徑。
def analyze(case, results):
    """Independently replay each accepted bundle and check combined inventories."""
    quota = {edge['id']: edge['quota'] for edge in case['contacts']}
    background = case['background']
    contacts = {edge['id']: edge for edge in case['contacts']}
    visits, schedules, routes, events = {}, [], [], []
    if len(results['records']) != len(case['bundles']):
        raise ValueError('Input/result bundle count mismatch')
    for bundle, record in zip(case['bundles'], results['records']):
        if record['bundle']['id'] != bundle['id']:
            raise ValueError('Input/result bundle order mismatch')
        if record['status'] != 'ACCEPTED':
            routes.append(dict(bundle=bundle['id'], status=record['status'],
                               node_path='', contact_path='', arrival='', delivery_delay=''))
            continue
        hops = [(cid, F(start)) for cid, start in record['hops']]
        check = evaluate_schedule(case, bundle, quota, background, hops)
        if not check['feasible'] or check['arrival'] != F(record['arrival']):
            raise ValueError(f'Same-model replay failure: {bundle["id"]}: {check}')
        visits[bundle['id']] = (bundle['size'], visits_for(case, bundle, hops))
        node_path = [bundle['source']] + [contacts[cid]['v'] for cid, _ in hops]
        routes.append(dict(bundle=bundle['id'], status='ACCEPTED',
                           node_path=' → '.join(node_path),
                           contact_path=' → '.join(cid for cid, _ in hops),
                           arrival=check['arrival'], delivery_delay=check['arrival']-bundle['g']))
        events.append(dict(time=bundle['g'], bundle=bundle['id'], hop=0,
                           contact='', node=bundle['source'], event='GENERATED'))
        for index, (cid, start) in enumerate(hops, 1):
            edge = contacts[cid]
            finish = start + bundle['size']/edge['rate']
            schedules.append(dict(bundle=bundle['id'], hop=index, contact=cid,
                                  sender=edge['u'], receiver=edge['v'], start=start,
                                  finish=finish, receive_start=start+edge['delay'],
                                  arrival=finish+edge['delay'], size=bundle['size']))
            for time, node, event in (
                (start, edge['u'], 'SEND_START'), (finish, edge['u'], 'SEND_FINISH'),
                (start+edge['delay'], edge['v'], 'RECEIVE_START'),
                (finish+edge['delay'], edge['v'], 'RECEIVE_FINISH')):
                events.append(dict(time=time, bundle=bundle['id'], hop=index,
                                   contact=cid, node=node, event=event))
        events.append(dict(time=check['arrival'], bundle=bundle['id'], hop=len(hops),
                           contact=hops[-1][0] if hops else '', node=bundle['dest'], event='DELIVERED'))
        quota, background = commit_independently(case, bundle, quota, background, hops)
    if quota != {key: F(value) for key, value in results['final_quota'].items()}:
        raise ValueError('Final remaining capacity mismatch')
    points = {F(0), case['horizon']}
    points.update(event['time'] for event in events)
    points.update(t for curves in case['background'].values() for curve in curves
                  for segment in curve for t in segment[:2] if 0 <= t <= case['horizon'])
    points = sorted(points)

    # 求指定節點及時間的占用，可選擇只計某一個 Bundle。
    def value(node, t, bundle_id=None):
        if bundle_id is None:
            return background_at(case['background'], node, t) + sum(
                (inventory(visit, t, size) for size, rows in visits.values()
                 for visit in rows if visit['node'] == node), F(0))
        size, rows = visits[bundle_id]
        return sum((inventory(visit, t, size) for visit in rows if visit['node'] == node), F(0))

    # 取得事件前後的占用值，區分交付前峰值與交付後釋放。
    def limits(node, index, bundle_id=None):
        """Exact one-sided limits by linear extrapolation within each event interval."""
        t = points[index]
        left = F(0)
        if index:
            p = points[index-1]
            left = 2*value(node, (p+3*t)/4, bundle_id)-value(node, (p+t)/2, bundle_id)
        right = F(0)
        if index+1 < len(points):
            q = points[index+1]
            right = 2*value(node, (3*t+q)/4, bundle_id)-value(node, (t+q)/2, bundle_id)
        else:
            # The one-sided limit at T must still show immediate delivery/release.
            future = [x for curves in case['background'].values() for curve in curves
                      for segment in curve for x in segment[:2] if x > t]
            q = min(future, default=t+1)
            right = 2*value(node, (3*t+q)/4, bundle_id)-value(node, (t+q)/2, bundle_id)
        return left, value(node, t, bundle_id), right

    samples, peaks, plot_values = [], [], {}
    for node, capacity in case['buffers'].items():
        best, when = F(0), F(0)
        lines = {'total': [], **{identifier: [] for identifier in visits}}
        for index, time in enumerate(points):
            total_limits = limits(node, index)
            for side, amount in zip(('left', 'event_peak', 'right'), total_limits):
                samples.append(dict(node=node, time=time, side=side, occupancy=amount, limit=capacity))
                if amount > best:
                    best, when = amount, time
            for key in lines:
                values = total_limits if key == 'total' else limits(node, index, key)
                lines[key].extend((time, amount) for amount in values)
        if best > capacity:
            raise ValueError(f'Combined buffer replay failure: {node}@{when}: {best}>{capacity}')
        peaks.append(dict(node=node, peak=best, peak_time=when, limit=capacity,
                          within_limit=best <= capacity))
        plot_values[node] = lines
    conflicts = []
    for index, first in enumerate(schedules):
        for second in schedules[index+1:]:
            if first['contact'] != second['contact']:
                continue
            start, end = max(first['start'], second['start']), min(first['finish'], second['finish'])
            if start < end:
                conflicts.append(dict(contact=first['contact'], bundle1=first['bundle'],
                                      hop1=first['hop'], bundle2=second['bundle'], hop2=second['hop'],
                                      overlap_start=start, overlap_end=end))
    event_order = dict(GENERATED=0, SEND_START=1, RECEIVE_START=2,
                       SEND_FINISH=3, RECEIVE_FINISH=4, DELIVERED=5)
    return dict(routes=routes, schedules=schedules, events=sorted(
        events, key=lambda e: (e['time'], e['bundle'], e['hop'], event_order[e['event']])),
        buffer_samples=samples, buffer_peaks=peaks, plot_values=plot_values,
        link_conflicts=conflicts, final_quota=quota, points=points)


# 繪製已算好的拓樸與占用曲線；不以圖片代替數值驗證。
def render(case, replay, output, positions=None):
    """Plot only after numerical checks; optional plotting dependencies stay here."""
    import sys
    dependencies = Path(__file__).resolve().parents[2]/'tmp/validation_plot_dependencies'
    try:
        import matplotlib
    except ModuleNotFoundError:
        if not dependencies.is_dir():
            raise RuntimeError('圖表輸出需要matplotlib；數值結果已保存在report資料夾')
        sys.path.insert(0, str(dependencies))
        import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Circle
    from matplotlib.font_manager import FontProperties, fontManager
    font = Path('C:/Windows/Fonts/kaiu.ttf')
    if font.exists():
        fontManager.addfont(str(font))
        plt.rcParams['font.family'] = [FontProperties(fname=str(font)).get_name(), 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    colors = ['#D97706', '#16743B', '#2563A6', '#7C3AED']
    nodes = list(case['buffers'])
    if positions is None:
        positions = {node: (math.cos(2*math.pi*i/len(nodes)), math.sin(2*math.pi*i/len(nodes)))
                     for i, node in enumerate(nodes)}
    if set(nodes) - positions.keys():
        raise ValueError('Position file lacks a node')
    count = Counter((edge['u'], edge['v']) for edge in case['contacts'])
    seen = Counter()
    radii = {}
    for edge in case['contacts']:
        pair = (edge['u'], edge['v'])
        radii[edge['id']] = (seen[pair]-(count[pair]-1)/2)*0.34
        seen[pair] += 1
    for index, route in enumerate(replay['routes']):
        if route['status'] != 'ACCEPTED':
            continue
        color = colors[index % len(colors)]
        selected = {row['contact']: row for row in replay['schedules'] if row['bundle']==route['bundle']}
        fig, ax = plt.subplots(figsize=(12, 6.6))
        ax.axis('off')
        for edge in case['contacts']:
            p, q = positions[edge['u']], positions[edge['v']]
            rad = radii[edge['id']]
            chosen = selected.get(edge['id'])
            col = color if chosen else '#BDC3CA'
            ax.add_patch(FancyArrowPatch(p, q, connectionstyle=f'arc3,rad={rad}',
                                        arrowstyle='-|>', mutation_scale=20, shrinkA=21, shrinkB=21,
                                        linewidth=3 if chosen else 1.2, color=col))
            x, y = (p[0]+q[0])/2, (p[1]+q[1])/2
            x += rad*(q[1]-p[1])/2
            y -= rad*(q[0]-p[0])/2
            label = f'{edge["id"]} [{edge["start"]},{edge["end"]})'
            if chosen:
                label += f'\n發送 {chosen["start"]}–{chosen["finish"]} 秒\n完整抵達 {chosen["arrival"]} 秒'
            ax.text(x, y, label, ha='center', va='center', fontsize=11 if chosen else 9,
                    color=col if chosen else '#858B93',
                    bbox=dict(facecolor='white', edgecolor='none', alpha=.95, pad=3))
        for node, (x,y) in positions.items():
            if node not in case['buffers']:
                continue
            ax.add_patch(Circle((x,y), .19, facecolor='white', edgecolor='#333399', lw=2))
            ax.text(x,y,node,ha='center',va='center',fontsize=17,color='#333399')
        xs, ys = zip(*(positions[node] for node in nodes))
        ax.set_xlim(min(xs)-.6,max(xs)+.6); ax.set_ylim(min(ys)-.65,max(ys)+.65)
        ax.set_aspect('equal')
        bundle = case['bundles'][index]
        fig.suptitle(f'{route["bundle"]}：{route["node_path"]}', fontsize=23, color='#333399')
        fig.text(.5,.035,f'S={bundle["size"]} MB，生成 {bundle["g"]} 秒，完整抵達 {route["arrival"]} 秒\n'
                 f'選定 contacts：{route["contact_path"]}；灰色為其他 contacts',
                 ha='center',fontsize=13,color='#333399')
        fig.subplots_adjust(top=.87,bottom=.14,left=.04,right=.96)
        fig.savefig(output/f'route_{index+1:02d}.png',dpi=160)
        fig.savefig(output/f'route_{index+1:02d}.svg')
        plt.close(fig)
    fig, axes = plt.subplots(math.ceil(len(nodes)/3),3,figsize=(14,3.7*math.ceil(len(nodes)/3)),squeeze=False)
    for node, ax in zip(nodes, axes.flat):
        lines = replay['plot_values'][node]
        for index, (identifier, values) in enumerate((k,v) for k,v in lines.items() if k!='total'):
            ax.plot([float(t) for t,y in values],[float(y) for t,y in values],
                    color=colors[index%len(colors)],lw=2.5,label=identifier)
        total = lines['total']
        ax.plot([float(t) for t,y in total],[float(y) for t,y in total],
                color='#222222',ls='--',lw=1.4,label='合計')
        capacity = float(case['buffers'][node])
        ax.axhline(capacity,color='#B32C28',ls=':',lw=1.5,label='上限')
        ax.set_title(f'{node} 的 buffer 占用',fontsize=16)
        ax.set_xlabel('時間（秒）');ax.set_ylabel('資料量（MB）')
        ax.set_xlim(0,float(case['horizon']));ax.set_ylim(-.15,max(capacity*1.25,.5))
        ax.grid(alpha=.15);ax.legend(fontsize=9)
    for ax in list(axes.flat)[len(nodes):]:
        ax.set_visible(False)
    fig.suptitle('選定兩包排程的接收、等待與逐 byte 釋放',fontsize=21,color='#333399')
    fig.tight_layout(rect=(0,0,1,.94))
    fig.savefig(output/'buffer_all_nodes.png',dpi=160)
    fig.savefig(output/'buffer_all_nodes.svg')
    plt.close(fig)
    # Keep exported SVG line endings portable for Git.
    for svg_path in output.glob('*.svg'):
        svg_text = '\n'.join(line.rstrip() for line in svg_path.read_text(encoding='utf8').splitlines()) + '\n'
        svg_path.write_text(svg_text, encoding='utf8', newline='\n')


# 載入已保存結果，先驗證完整排程，再輸出數值重播表與報告。
def generate(run_dir, positions_path=None, draw=True):
    run_dir=Path(run_dir)
    case=load_scenario(run_dir/'input.json')
    results=json.loads((run_dir/'results.json').read_text(encoding='utf8'))
    output=run_dir/'report'
    output.mkdir(exist_ok=False)
    try:
        replay=analyze(case,results)
    except ValueError as error:
        write_json(output/'failure.json',dict(reason=str(error),case=case,results=results))
        raise
    write_csv(output/'routes.csv',['bundle','status','node_path','contact_path','arrival','delivery_delay'],replay['routes'])
    write_csv(output/'events.csv',['time','bundle','hop','contact','node','event'],replay['events'])
    write_csv(output/'buffer_peaks.csv',['node','peak','peak_time','limit','within_limit'],replay['buffer_peaks'])
    write_csv(output/'buffer_events.csv',['node','time','side','occupancy','limit'],replay['buffer_samples'])
    write_csv(output/'link_conflicts.csv',['contact','bundle1','hop1','bundle2','hop2','overlap_start','overlap_end'],replay['link_conflicts'])
    write_json(output/'replay_check.json',dict(
        same_model_schedule_checks='PASS',buffer_peaks=replay['buffer_peaks'],
        final_quota=replay['final_quota'],link_conflicts=replay['link_conflicts'],
        contact_interval_overlap_checked=True,shared_radio_checked=False,
        routing_algorithm_changed=False,real_bundle_protocol_execution=False,
        note='Interval conflicts are model-boundary diagnostics, not automatically repaired.'))
    lines=['# PPT拓樸執行結果','',
           '依固定順序規劃兩包，再依選定發送時間做分段線性的排程重播。',
           'Buffer使用原模型的事件峰值約定；同時事件在CSV的排序不代表新的處理優先序。','',
           '| Bundle | Node路徑 | Contacts | 完整抵達（秒） | 生成至交付（秒） |',
           '|---|---|---|---|---|']
    for route in replay['routes']:
        lines.append(f'| {route["bundle"]} | {route["node_path"]} | {route["contact_path"]} | {route["arrival"]} | {route["delivery_delay"]} |')
    lines.extend(['','## 每跳傳送','',
                  '| Bundle | Contact | Sender→Receiver | 發送起訖 | 接收起訖 |','|---|---|---|---|---|'])
    for row in replay['schedules']:
        lines.append(f'| {row["bundle"]} | {row["contact"]} | {row["sender"]}→{row["receiver"]} | {row["start"]}–{row["finish"]} | {row["receive_start"]}–{row["arrival"]} |')
    lines.extend(['','## 檢查結果','',
                  '- 同模型完整排程與資源更新：通過。',
                  '- 所有節點的buffer峰值與上限，見buffer_peaks.csv。',
                  f'- 選定傳輸的同contact時間重疊：{len(replay["link_conflicts"])}筆。',
                  '- 這是此案例的事後檢查，沒有將transmission calendar加入路由搜尋。',
                  '- 未模擬實際Bundle Protocol、共用radio、遺失、重傳或控制指令延遲。',
                  '- 已在原執行入口啟用完整搜尋的案例，可在results.json查看oracle_checked。',''])
    (output/'report.md').write_text('\n'.join(lines),encoding='utf8',newline='\n')
    if draw:
        positions=None if positions_path is None else json.loads(Path(positions_path).read_text(encoding='utf8'))
        render(case,replay,output,positions)
    return output


# 命令列可選擇只輸出數值報告，不必載入繪圖套件。
def main():
    parser=argparse.ArgumentParser(description='依路由結果重播排程，輸出路徑與buffer圖')
    parser.add_argument('--run',required=True,type=Path)
    parser.add_argument('--positions',type=Path,help='節點座標JSON；省略時使用圓形配置')
    parser.add_argument('--no-figures',action='store_true',help='只輸出數值表，不需要matplotlib')
    args=parser.parse_args()
    print(generate(args.run,args.positions,draw=not args.no_figures))


if __name__=='__main__':
    main()
