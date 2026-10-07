"""Plot B occupancy for the infeasible c3-to-c5 candidate shown in the PPT.
This candidate is rejected; it is not an accepted reservation.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp' / 'validation_plot_dependencies'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

OUT = ROOT / 'output' / 'figures' / 'buffer_early_arrival_full_timeline_v02_20261007'
OUT.mkdir(parents=True, exist_ok=True)
font = FontProperties(fname='C:/Windows/Fonts/kaiu.ttf', size=17)
fig, ax = plt.subplots(figsize=(8, 3.5), dpi=200)
times = [0, 1, 2, 3, 6, 7, 10, 11, 12]
first = [0, 0, 0, 4, 4, 0, 0, 0, 0]
second = [0, 0, 4, 4, 4, 4, 4, 0, 0]
total = [a + b for a, b in zip(first, second)]
assert total == [0, 0, 4, 8, 8, 4, 4, 0, 0]
ax.plot(times, first, color='#cb6507', lw=2.6, label='第一包')
ax.plot(times, total, color='#be2929', lw=2.6, label='合計')
ax.plot(times, second, color='#2465a5', lw=2.4, ls='--', label='第二包（候選）')
ax.legend(prop=FontProperties(fname='C:/Windows/Fonts/kaiu.ttf',size=12),
          loc='upper center', bbox_to_anchor=(.5,1.24), ncol=3, frameon=False)
ax.axhline(4, color='#666666', lw=1, zorder=0)
ax.text(9.4, 4.3, '上限 4', fontproperties=font, color='#666666')
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.3)
ax.set_xticks(range(0, 13, 1))
ax.set_yticks([0, 4, 8])
ax.spines[['top', 'right']].set_visible(False)
for side in ['left', 'bottom']:
    ax.spines[side].set_color('#666666')
    ax.spines[side].set_linewidth(1)
ax.tick_params(axis='both', colors='#666666', labelsize=15, length=3, pad=7)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(font)
ax.text(1.035, -.08, '秒', transform=ax.transAxes, fontproperties=font, color='#666666')
fig.subplots_adjust(left=.09, right=.92, bottom=.20, top=.82)
fig.savefig(OUT / 'buffer_early_arrival_full_timeline.png', dpi=240, facecolor='white')
fig.savefig(OUT / 'buffer_early_arrival_full_timeline.svg', facecolor='white')
plt.close(fig)
svg = OUT / 'buffer_early_arrival_full_timeline.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf8').splitlines())+'\n', encoding='utf8', newline='\n')
print(OUT)

import csv
with (OUT/'buffer_curve_points.csv').open('w',encoding='utf8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n')
    writer.writerow(['time_s','first_MB','second_candidate_MB','total_MB'])
    writer.writerows(zip(times,first,second,total))
