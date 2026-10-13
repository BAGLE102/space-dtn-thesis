"""以實際輸出排程繪製Buffer曲線與contact預約時間軸。"""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from src.validation.model import normalize, route_curves, occupancy, number


def side_value(background, node, t, side):
    """畫出事件前／事件點／事件後的值，保留生成與交付時的瞬間峰值。"""
    if side=='at':
        return occupancy(background,node,t)
    total=F(0)
    for curve in background.get(node,[]):
        values=[]
        for lo,hi,y0,y1 in curve:
            included = (lo<t<=hi) if side=='left' else (lo<=t<hi)
            if lo<hi and included:
                values.append(y0+(y1-y0)*(t-lo)/(hi-lo))
        total+=max(values,default=F(0))
    return total


def series(background,node,points):
    return ([float(t) for t in points for _ in range(3)],
            [float(side_value(background,node,t,side)) for t in points
             for side in ('left','at','right')])


def generate(output, nodes=None, time_origin=0, buffer_zoom=False):
    output=Path(output)
    origin=float(time_origin)
    xlabel='Time (s)' if origin==0 else f'Time since {origin:g} s (s)'
    raw=json.loads((output/'results.json').read_text(encoding='utf-8'))
    case=normalize(json.loads((output/'input.json').read_text(encoding='utf-8')))
    total={v:[[[number(x) for x in seg] for seg in curve] for curve in curves]
           for v,curves in raw['background'].items()}
    records=raw['records']; own=[]
    for record in records:
        if record['arrival'] is not None:
            b=next(b for b in case['bundles'] if b['id']==record['bundle']['id'])
            hops=[(cid,F(s)) for cid,s in record['hops']]
            own.append((b['id'],route_curves(case,b,hops)))
    points=sorted({F(0),case['horizon']}|{t for curves in total.values()
                  for curve in curves for seg in curve for t in seg[:2]})
    figures=output/'figures'; figures.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    nodes=list(case['buffers']) if nodes is None else list(nodes)
    if not nodes or any(n not in case['buffers'] for n in nodes):
        raise ValueError('INVALID_FIGURE_NODES')
    columns=2; rows=(len(nodes)+1)//2
    fig,axs=plt.subplots(rows,columns,figsize=(13,3*rows),squeeze=False)
    palette=['#d16b06','#246bb1','#1c9254','#a84ba0','#8a6505']
    for ax,node in zip(axs.flat,nodes):
        for i,(bid,curves) in enumerate(own):
            x,y=series(curves,node,points)
            ax.plot([t-origin for t in x],y,color=palette[i%len(palette)],lw=1.7,alpha=.85,label=bid)
        x,y=series(total,node,points)
        ax.plot([t-origin for t in x],y,color='#222222',lw=2.2,label='total',linestyle='--')
        limit=float(case['buffers'][node])
        upper=max(max(y,default=0)*1.18,.12) if buffer_zoom else max(limit,max(y,default=0))*1.18
        if limit<=upper:
            ax.axhline(limit,color='#777777',lw=1.4,label='limit')
        else:
            ax.text(.97,.92,f'Capacity {limit:g} MB (above plot range)',
                    transform=ax.transAxes,ha='right',color='#666666',fontsize=10)
        ax.set(xlim=(0,float(case['horizon'])-origin),ylim=(-upper*.03,upper),
               title=f'Node {node}',xlabel=xlabel,ylabel='Buffer occupancy (MB)')
        ax.grid(alpha=.2)
    for ax in list(axs.flat)[len(nodes):]: ax.axis('off')
    handles,labels=axs.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=min(len(labels),7),bbox_to_anchor=(.5,0))
    fig.suptitle('Accepted bundle reservations (instantaneous delivery peaks included)',fontsize=15)
    fig.tight_layout(rect=(0,.035,1,.965))
    fig.savefig(figures/'buffer_occupancy.png',dpi=160)
    fig.savefig(figures/'buffer_occupancy.svg')
    plt.close(fig)
    # 每個contact獨立一列；不同contact共用硬體互斥不在此模型。
    contacts=case['contacts']; fig,ax=plt.subplots(figsize=(13,max(4,len(contacts)*.4)))
    colors={bid:palette[i%len(palette)] for i,(bid,_) in enumerate(own)}
    for i,c in enumerate(contacts):
        ax.broken_barh([(float(c['start'])-origin,float(c['end']-c['start']))],(i-.32,.64),facecolors='#e6e6ed')
        for entry in raw['calendar'].get(c['id'],[]):
            s,f=F(entry['start']),F(entry['finish'])
            ax.broken_barh([(float(s)-origin,float(f-s))],(i-.23,.46),facecolors=colors[entry['bundle']])
    ax.set_yticks(range(len(contacts)),[f'{c["id"]}: {c["u"]} -> {c["v"]}' for c in contacts])
    ax.invert_yaxis(); ax.set(xlim=(0,float(case['horizon'])-origin),xlabel=xlabel)
    ax.set_title('Contact windows and accepted transmission reservations',pad=46)
    ax.legend(handles=[Patch(facecolor='#e6e6ed',label='contact window')] +
              [Patch(facecolor=color,label=bid) for bid,color in colors.items()],
              loc='lower center',bbox_to_anchor=(.5,1.035),ncol=len(colors)+1,fontsize=9)
    ax.grid(axis='x',alpha=.2); fig.tight_layout()
    fig.savefig(figures/'contact_reservations.png',dpi=160)
    fig.savefig(figures/'contact_reservations.svg'); plt.close(fig)
    # Matplotlib在Windows可能輸出CRLF，統一SVG換行便於Git檢查。
    for svg in figures.glob('*.svg'):
        svg.write_bytes(b'\n'.join(line.rstrip() for line in svg.read_bytes().splitlines())+b'\n')
    print(figures)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    generate(parser.parse_args().output)
