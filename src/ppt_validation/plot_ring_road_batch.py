"""批次查詢完成狀態圖：未處理不能畫成無路徑。"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate(output):
    output=Path(output)
    rows=json.loads((output/'batch_results.json').read_text(encoding='utf-8'))
    labels=[r['case']+(' *' if r['status']!='COMPLETE' else '') for r in rows]
    accepted=[r['accepted'] for r in rows]
    no_route=[r['no_route'] for r in rows]
    pending=[r['unprocessed'] for r in rows]
    fig,ax=plt.subplots(figsize=(12,7))
    ax.barh(labels,accepted,color='#21834b',label='Verified feasible')
    ax.barh(labels,no_route,left=accepted,color='#cb7640',label='Verified no route')
    ax.barh(labels,pending,left=[a+b for a,b in zip(accepted,no_route)],
            color='#d9dce3',label='Unprocessed (no conclusion)')
    ax.invert_yaxis();ax.set(xlabel='Number of bundles',
        title='Ring Road diagnostic batches: verified queries and incomplete work')
    ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='lower right',fontsize=9)
    fig.text(.99,.015,'* Entire job reached its 20 s limit; checked queries remain valid',
             ha='right',fontsize=10,color='#555555')
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(output/'batch_query_states.png',dpi=160)
    svg=output/'batch_query_states.svg';fig.savefig(svg);plt.close(fig)
    svg.write_bytes(b'\n'.join(line.rstrip() for line in svg.read_bytes().splitlines())+b'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    generate(parser.parse_args().output)
