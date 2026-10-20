"""建立PPT兩包拓譜的長contact版本；只準備輸入與圖，不執行路由。"""
from collections import defaultdict
import csv
import json
from pathlib import Path

from .config import load_scenario

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT/'configs/long_contacts_20261021'
OUTPUT = ROOT/'output/long_contacts_20261021'
# 同一對端點的兩條contact不重疊，避免默認成兩個獨立平行通道。
WINDOWS = [(2,12),(8,18),(1,11),(12,28),(20,36),(1,18),(16,30),(4,14)]


def write_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',
                    encoding='utf-8',newline='\n')


def write_csv(path, fields, rows):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def prepare():
    CONFIG.mkdir(parents=True,exist_ok=True);OUTPUT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'configs/walkthrough_contacts.csv').open(encoding='utf-8-sig') as stream:
        original=list(csv.DictReader(stream))
    contacts=[];controlled=[];comparison=[]
    for old,(start,end) in zip(original,WINDOWS,strict=True):
        c=dict(old,start=str(start),end=str(end))
        capacity=int(c['rate'])*(end-start)
        c['remaining_capacity']=str(capacity)
        contacts.append(c)
        controlled.append(dict(c,remaining_capacity=old['remaining_capacity']))
        comparison.append(dict(contact=c['id'],sender=c['source'],receiver=c['target'],
            old_start=old['start'],old_end=old['end'],new_start=start,new_end=end,
            duration=end-start,rate=c['rate'],delay=c['delay'],
            full_initial_capacity=capacity,controlled_residual=old['remaining_capacity']))
    fields=list(original[0])
    write_csv(CONFIG/'contacts.csv',fields,contacts)
    write_csv(CONFIG/'contacts_same_quota.csv',fields,controlled)
    topology=json.loads((ROOT/'configs/ppt_modular/topology.json').read_text(encoding='utf-8'))
    topology['contacts_file']='contacts.csv';write_json(CONFIG/'topology.json',topology)
    topology['contacts_file']='contacts_same_quota.csv'
    write_json(CONFIG/'topology_same_quota.json',topology)
    demands=json.loads((ROOT/'configs/ppt_modular/bundles.json').read_text(encoding='utf-8'))
    write_json(CONFIG/'bundles.json',demands)
    checks=[]
    for suffix in ['', '_same_quota']:
        experiment=dict(schema_version=2,name='long_contacts'+suffix,
            topology_file='topology'+suffix+'.json',bundles_file='bundles.json',
            algorithm='interval_candidate_not_implemented',time_step='1',horizon='40')
        # time_step僅為既有輸入格式的相容欄位，不表示新版須逐秒起送。
        filename='experiment'+suffix+'.json';write_json(CONFIG/filename,experiment)
        case=load_scenario(CONFIG/filename)
        assert len(case['contacts'])==8 and len(case['buffers'])==5
        assert all(c['end']-c['start']>=10 for c in case['contacts'])
        pairs=defaultdict(list)
        for c in case['contacts']:pairs[c['u'],c['v']].append(c)
        for values in pairs.values():
            ordered=sorted(values,key=lambda c:c['start'])
            assert all(a['end']<=b['start'] for a,b in zip(ordered,ordered[1:]))
        checks.append(dict(config=filename,contacts=8,nodes=5,bundles=2,
                           input_valid=True,routing_executed=False))
    write_csv(OUTPUT/'contact_comparison.csv',list(comparison[0]),comparison)
    write_json(OUTPUT/'input_validation.json',dict(checks=checks,
        scope='Input validation only. No interval solver or enumeration was run.'))
    draw(contacts)
    return comparison


def draw(contacts):
    """標楷體科學圖：左側連接、右側完整時窗，所有時間由0開始。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import FancyArrowPatch
    font=FontProperties(fname='C:/Windows/Fonts/kaiu.ttf')
    fig,(graph,timeline)=plt.subplots(1,2,figsize=(16,8.5),
                                   gridspec_kw={'width_ratios':[1,1.2]})
    positions={'X':(0,3),'A':(0,0),'B':(2.6,2.5),'C':(2.6,.2),'D':(5.2,1.4)}
    grouped=defaultdict(list)
    for c in contacts:grouped[c['source'],c['target']].append(c)
    for (u,v),values in grouped.items():
        x,y=positions[u];xx,yy=positions[v]
        graph.add_patch(FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',
            mutation_scale=20,linewidth=2,color='#333399',shrinkA=26,shrinkB=26))
        label='\n'.join(f"{c['id']}：{c['start']}～{c['end']} 秒" for c in values)
        graph.text((x+xx)/2,(y+yy)/2+.20,label,fontproperties=font,fontsize=15,
                   ha='center',va='bottom',color='#333399',
                   bbox=dict(facecolor='white',edgecolor='none',alpha=.9,pad=2))
    for node,(x,y) in positions.items():
        graph.scatter(x,y,s=1600,color='white',edgecolor='#333399',linewidth=2,zorder=4)
        graph.text(x,y,node,fontproperties=font,fontsize=24,ha='center',va='center',zorder=5)
    graph.set_xlim(-.7,6);graph.set_ylim(-1.3,4);graph.axis('off')
    graph.set_title('長 contact 拓譜：沿用原節點與連線',fontproperties=font,fontsize=22,pad=15)
    graph.text(-.4,-.8,'節點 Buffer：4 MB；每包：4 MB\n'
               '第一包 X→D（g=0）；第二包 A→D（g=1）',
               fontproperties=font,fontsize=15,color='#333333')
    for i,c in enumerate(contacts):
        start,end=int(c['start']),int(c['end'])
        timeline.broken_barh([(start,end-start)],(i-.22,.44),facecolors='#246BB1')
        timeline.text((start+end)/2,i,f'{start}～{end}',ha='center',va='center',
                      fontproperties=font,fontsize=14,color='white')
    timeline.set_yticks(range(8),[f"{c['id']} {c['source']}→{c['target']}" for c in contacts],
                       fontproperties=font,fontsize=15)
    timeline.invert_yaxis();timeline.set_xlim(0,40);timeline.set_xticks(range(0,41,5))
    timeline.set_xlabel('時間（秒）',fontproperties=font,fontsize=16)
    timeline.set_title('Contact Plan：每條時窗長 10～17 秒',fontproperties=font,fontsize=22,pad=15)
    timeline.grid(axis='x',alpha=.22)
    fig.text(.52,.04,'速率均為 4 MB/s；δ(c2,c5,c6)=1 秒，其餘為 0。\n'
             '此圖為測試輸入，尚未計算路徑或建立 Buffer 預約。',
             fontproperties=font,fontsize=14,color='#444444')
    fig.tight_layout(rect=(0,.12,1,1))
    fig.savefig(OUTPUT/'long_contact_topology.png',dpi=160)
    svg=OUTPUT/'long_contact_topology.svg';fig.savefig(svg)
    svg.write_text('\n'.join(x.rstrip() for x in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8',newline='\n')
    plt.close(fig)


if __name__=='__main__':
    prepare()
