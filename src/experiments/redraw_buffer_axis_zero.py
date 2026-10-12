# 歷史圖片重繪工具：曲線取自圖片，不是新增模擬或補推未提供的數值。
"""Redraw the visible chart with an x-axis starting at zero.
Coordinates are transcribed from the supplied image, not simulation outputs.
No curve values are inferred before t=2.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp' / 'validation_plot_dependencies'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

OUT = ROOT / 'output' / 'figures' / 'buffer_chart_axis_zero_20261007'
OUT.mkdir(parents=True, exist_ok=True)
font = FontProperties(fname='C:/Windows/Fonts/kaiu.ttf', size=17)
fig, ax = plt.subplots(figsize=(8, 3.5), dpi=200)
ax.plot([2, 3, 6, 7, 12], [0, 4, 4, 0, 0], color='#cb6507', lw=2.6)
ax.plot([2, 10, 11, 12], [4, 4, 0, 0], color='#2465a5', lw=2.6)
ax.plot([2, 3, 6, 7, 10, 11, 12], [4, 8, 8, 4, 4, 0, 0], color='#be2929', lw=2.6)
ax.axhline(4, color='#666666', lw=1, zorder=0)
ax.text(9.4, 4.3, '上限 4', fontproperties=font, color='#666666')
ax.set_xlim(0, 12)
ax.set_ylim(0, 9.3)
ax.set_xticks(range(0, 13, 2))
ax.set_yticks([0, 4, 8])
ax.spines[['top', 'right']].set_visible(False)
for side in ['left', 'bottom']:
    ax.spines[side].set_color('#666666')
    ax.spines[side].set_linewidth(1)
ax.tick_params(axis='both', colors='#666666', labelsize=15, length=3, pad=7)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(font)
ax.text(1.035, -.08, '秒', transform=ax.transAxes, fontproperties=font, color='#666666')
fig.subplots_adjust(left=.09, right=.92, bottom=.20, top=.95)
fig.savefig(OUT / 'buffer_chart_axis_zero.png', dpi=240, facecolor='white')
fig.savefig(OUT / 'buffer_chart_axis_zero.svg', facecolor='white')
plt.close(fig)
svg = OUT / 'buffer_chart_axis_zero.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf8').splitlines())+'\n', encoding='utf8', newline='\n')
print(OUT)
