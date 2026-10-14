"""建立人工診斷拓譜與隔離案例；不更動待測路由或支配規則。

執行：python -m src.ppt_validation.diagnostic_suite
加 --run 才執行完整排程核對與小規模獨立列舉。
"""
import argparse
from copy import deepcopy
from pathlib import Path

from src.experiments.config import load_scenario
from .run import run, write_csv, write_json
from .temporal_reference import solve_temporal

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'configs/diagnostic_topology_20261014'


def edge(cid, u, v, start, end, rate=1, delay=0, quota=None):
    return dict(id=cid, u=u, v=v, start=start, end=end, rate=rate,
                delay=delay, quota=rate*(end-start) if quota is None else quota)


def bundle(bid, source, dest, release=0, size=1):
    return dict(id=bid, source=source, dest=dest, g=release, size=size)


def large_case():
    """12節點、32條有向contacts；長短時窗、回程及共同瓶頸並存。"""
    rows = [
        ('S1','A',0,2), ('S1','B',1,3), ('S2','A',0,2), ('S2','C',1,3),
        ('S3','B',0,2), ('S3','C',2,4),
        ('A','D',3,5), ('A','E',5,7), ('B','D',4,6), ('B','E',3,5),
        ('C','E',4,6), ('C','F',3,5),
        ('D','G',7,9), ('E','G',6,8), ('E','H',8,10), ('F','H',6,8),
        ('G','T',10,12), ('H','T',10,12),
        ('D','A',6,8), ('E','B',6,8), ('F','C',6,8), ('G','E',9,11),
        ('A','D',9,11), ('B','E',10,12), ('C','F',9,11),
        ('D','G',12,14), ('E','H',13,15), ('F','H',12,14),
        ('G','T',16,18), ('H','T',17,19),
        ('S1','T',0,2), ('E','T',14,15),
    ]
    contacts = [edge(f'c{i:02}', *row) for i, row in enumerate(rows, 1)]
    # c31低速，1MB即需4秒，容量與時窗不足；c32有非零傳播延遲。
    contacts[30].update(rate='1/4', quota='1/2')
    contacts[31]['delay'] = 2
    return dict(name='synthetic_12nodes_32contacts_5bundles', delta=1, horizon=24,
                algorithm='ppt_validation_no_dominance',
                buffers={v: (4 if v.startswith('S') or v == 'T' else 2)
                         for v in ['S1','S2','S3','A','B','C','D','E','F','G','H','T']},
                background={}, contacts=contacts,
                bundles=[bundle('b1','S1','T'), bundle('b2','S2','T'),
                         bundle('b3','S3','T'), bundle('b4','S1','T',1),
                         bundle('b5','S2','T',1,2)])


def focused_cases():
    """預期抵達時間由小案例人工推導；不是用待測搜尋產生答案。"""
    base = dict(name='normal', delta=1, horizon=6, buffers={'A':1,'B':1},
                background={}, contacts=[edge('ab','A','B',0,4)],
                bundles=[bundle('b1','A','B')])
    cases = []

    def add(name, expected, mutate=lambda c: None):
        case = deepcopy(base)
        case['name'] = name
        mutate(case)
        cases.append((case, expected))

    add('01_normal', [1])
    add('02_capacity_insufficient', [None], lambda c: c['contacts'][0].update(quota=0))
    add('03_exact_capacity', [1], lambda c: c['contacts'][0].update(quota=1))
    add('04_receiver_busy_then_free', [3],
        lambda c: c.update(background={'B':[[[0,2,1,1]]]}))
    add('05_receiver_interior_peak', [2],
        lambda c: c.update(background={'B':[[[0,'1/2',0,1],['1/2',1,1,0]]]}))
    add('06_receive_while_previous_drains', [1],
        lambda c: c.update(background={'B':[[[0,1,1,0]]]}))

    def waiting(c):
        c['contacts'][0].update(start=3, quota=1)
        c['background'] = {'A':[[[1,2,0,1],[2,3,1,0]]]}
    add('07_sender_waiting_overflow', [None], waiting)
    add('08_propagation_exceeds_deadline', [None],
        lambda c: (c.update(horizon=2), c['contacts'][0].update(end=1,quota=1,delay=2)))
    add('09_exact_window_end', [1],
        lambda c: c['contacts'][0].update(end=1, quota=1))
    add('10_bundle_exceeds_window', [None],
        lambda c: (c.update(buffers={'A':2,'B':2}),
                   c['bundles'][0].update(size=2),
                   c['contacts'][0].update(end=1,quota=1)))

    def sequential(c):
        c['buffers'] = {'A':2,'B':2}
        c['bundles'].append(bundle('b2','A','B'))
    add('11_sequential_transmission_reservation', [1,2], sequential)

    def later(c):
        c.update(buffers={'A':1,'B':1,'D':1}, horizon=4,
                 background={'B':[[[1,2,0,1],[2,3,1,0]]]},
                 contacts=[edge('ab','A','B',0,3),edge('bd','B','D',3,4)],
                 bundles=[bundle('b1','A','D')])
    add('12_late_arrival_needed', [4], later)
    return cases


def build_inputs():
    CONFIG.mkdir(parents=True, exist_ok=True)
    case = large_case()
    write_json(CONFIG/'topology_5bundles.json', case)
    write_csv(CONFIG/'contacts.csv', ['id','u','v','start','end','rate','delay','quota'],
              case['contacts'])
    write_csv(CONFIG/'bundles.csv', ['id','source','dest','g','size'], case['bundles'])
    manifest = []
    for item, expected in focused_cases():
        filename = item['name']+'.json'
        write_json(CONFIG/filename, item)
        manifest.append(dict(file=filename, expected_arrivals=expected))
    write_json(CONFIG/'focused_manifest.json', manifest)
    return manifest


def draw_topology(output):
    """圖上顯示連接與Buffer；右側完整列出contact時間與參數。"""
    from collections import defaultdict
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch
    case = large_case()
    positions = {'S1':(0,3), 'S2':(0,2), 'S3':(0,1),
                 'A':(2,3), 'B':(2,2), 'C':(2,1),
                 'D':(4,3), 'E':(4,2), 'F':(4,1),
                 'G':(6,2.7), 'H':(6,1.3), 'T':(8,2)}
    colors = ['#2573b8', '#de7919', '#338a58', '#7d54ad', '#777777']
    fig, (graph, timeline) = plt.subplots(1, 2, figsize=(18,11),
                                        gridspec_kw={'width_ratios':[1.1,1]})
    grouped = defaultdict(list)
    for c in case['contacts']:
        grouped[c['u'],c['v']].append(c)
    for (u,v), contacts in grouped.items():
        x,y = positions[u]; xx,yy = positions[v]
        reverse = xx < x
        color = colors[1] if reverse else colors[0]
        rad = .27 if reverse else (.12 if y != yy else .02)
        if (u,v) == ('S1','T'):
            rad = -.4
        if (u,v) == ('E','T'):
            rad = -.3
        graph.add_patch(FancyArrowPatch((x,y),(xx,yy),
            connectionstyle=f'arc3,rad={rad}',arrowstyle='-|>',
            mutation_scale=13,linewidth=1.3,color=color,shrinkA=24,shrinkB=24))
        # 每對端點列一次ID；實際時窗在右側逐條呈現。
        label = '/'.join(c['id'] for c in contacts)
        text_position = ((x+xx)/2, (y+yy)/2-rad*(xx-x)/2)
        if (u,v) == ('S1','T'):
            text_position = (4,3.4)
        elif (u,v) == ('E','T'):
            text_position = (6,2.32)
        graph.text(*text_position, label,
                   fontsize=8,color=color,ha='center',va='center',
                   bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))
    for node,(x,y) in positions.items():
        graph.scatter(x,y,s=1300,color='white',edgecolor='#29384f',linewidth=2,zorder=4)
        graph.text(x,y,node,ha='center',va='center',fontsize=14,zorder=5)
        graph.text(x,y-.26,f"Buffer {case['buffers'][node]} MB",
                   ha='center',va='top',fontsize=8)
    graph.set_xlim(-.8,8.7); graph.set_ylim(-.1,4.6); graph.axis('off')
    graph.set_title('Synthetic diagnostic topology\n12 nodes / 32 directed contacts / 5 bundles',fontsize=15)
    graph.text(0,.15,'Blue: forward contacts   Orange: return contacts\n'
               'Repeated endpoint pairs retain separate contact IDs.\n'
               'Bundles: b1 S1 / b2 S2 / b3 S3 / b4 S1 / b5 S2 -> T\n'
               'Sizes: 1, 1, 1, 1, 2 MB; release times: 0, 0, 0, 1, 1 s.\n'
               'Artificial input; not a NASA or operational topology.',fontsize=10)
    for index,c in enumerate(case['contacts']):
        start,end = c['start'],c['end']
        color=colors[1] if positions[c['v']][0]<positions[c['u']][0] else colors[0]
        timeline.broken_barh([(start,end-start)],(index-.3,.6),facecolors=color)
        timeline.text(end+.2,index,
            f"r={c['rate']}, d={c['delay']}, R={c['quota']}",fontsize=7,va='center')
    timeline.set_yticks(range(32),[f"{c['id']}  {c['u']} -> {c['v']}" for c in case['contacts']],fontsize=8)
    timeline.invert_yaxis(); timeline.set_xlim(0,25)
    timeline.set_xlabel('Sender transmission window (s)')
    timeline.set_title('Contact Plan: rate r (MB/s), delay d (s), initial quota R (MB)',fontsize=11)
    timeline.grid(axis='x',alpha=.2)
    fig.tight_layout()
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/'topology_and_contacts.png',dpi=160)
    svg=output/'topology_and_contacts.svg'
    fig.savefig(svg)
    # 保持可攜的LF及無尾端空白，方便Git檢查。
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8',newline='\n')
    plt.close(fig)


def execute(output):
    """任一同模型不一致由run停止；人工預期不一致另存證據再停止。"""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    results = []
    try:
        for item in build_inputs():
            case = load_scenario(CONFIG/item['file'])
            records = run(case, output/case['name'], reference_solver=solve_temporal)['records']
            actual = [r['arrival'] for r in records]
            if actual != item['expected_arrivals']:
                write_json(output/'failure.json', dict(case=case['name'],
                    expected=item['expected_arrivals'], actual=actual))
                raise RuntimeError('MANUAL_EXPECTATION_MISMATCH: 停止，未修改演算法')
            results.append(dict(case=case['name'], arrivals=actual, status='VERIFIED'))
        case = load_scenario(CONFIG/'topology_5bundles.json')
        records = run(case, output/'large_5bundles', reference_solver=solve_temporal)['records']
        results.append(dict(case=case['name'], status='VERIFIED',
                            arrivals=[r['arrival'] for r in records]))
    except Exception as error:
        # 資源上限是未完成，不等於無路徑；同模型錯誤證據保留在子目錄。
        write_json(output/'suite_status.json', dict(status='STOP_OR_INCOMPLETE',
            reason=str(error), completed=results, performance_comparison_allowed=False))
        raise
    draw_topology(output)
    write_json(output/'suite_status.json', dict(status='COMPLETE', completed=results,
        scope='finite-grid current PPT verification; no dynamic-contact implementation'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--output', type=Path,
                        default=ROOT/'output/diagnostic_topology_20261014')
    args = parser.parse_args()
    if args.run:
        execute(args.output)
    else:
        build_inputs()
