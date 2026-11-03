#!/usr/bin/env python3
"""contact 吃緊實驗的簡報圖與統計。用法：python3 make_tight_figure.py performance.jsonl out_dir"""
import json
import os
import statistics as st
import sys

import matplotlib.pyplot as plt

import make_ppt_figures as F

CELLS = [("tight_20n", 100), ("tight_20n", 300), ("tight_40n", 100), ("tight_40n", 300)]


def main():
    path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    R = F.load(path)
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.35), sharey=True)
    w = .26
    for ax, M, tag in zip(axs, (15, 150), ("Buffer = 15 MB（3 包）", "Buffer = 150 MB（30 包）")):
        for j, me in enumerate(F.ORDER):
            xs, ys, es = [], [], []
            for i, (t, n) in enumerate(CELLS):
                v = [F.delivery(r) for r in F.get(R, t, n, M, me)]
                xs.append(i + (j - 1) * w)
                ys.append(st.mean(v))
                es.append(F.ci(v))
                print(t, n, M, me, "%.1f±%.1f" % (ys[-1], es[-1]))
            ax.bar(xs, ys, w * .92, color=F.COL[me], label=F.LAB[me], yerr=es,
                   error_kw={"ecolor": "#333333", "elinewidth": 1, "capsize": 2.5})
            for x, y, e in zip(xs, ys, es):
                if M == 15 or y < 100:
                    ax.text(x, y + e + 1.5, "%.1f" % y, ha="center", va="bottom", fontsize=10.5, color="#222222")
        ax.set_xticks(range(4))
        ax.set_xticklabels(F.XT)
        ax.set_ylim(0, 122)
        ax.set_yticks(range(0, 101, 20))
        ax.set_title(tag, color="#222222")
        F.grid(ax)
    axs[1].text(.5, .985, "未標數字的長條都是 100%", transform=axs[1].transAxes, ha="center", va="top", fontsize=12.5, color="#222222")
    axs[0].set_ylabel("送達率（%）")
    axs[0].legend(loc="lower center", ncol=3, frameon=False, fontsize=12.5, bbox_to_anchor=(1.05, -.34))
    fig.subplots_adjust(left=.065, right=.995, top=.92, bottom=.24, wspace=.05)
    fig.savefig(os.path.join(out, "fig_tight.png"), dpi=220)
    for M in (15, 150):
        wins = {b: [0, 0, 0] for b in ("sr1", "sr10")}
        for t, n in CELLS:
            ours = F.get(R, t, n, M, "ours")
            for b in wins:
                for a, c in zip(ours, F.get(R, t, n, M, b)):
                    x, y = F.delivery(a), F.delivery(c)
                    wins[b][0 if x > y else 1 if x == y else 2] += 1
        print("M", M, "W/T/L", wins)
    for t, n in CELLS:
        for M in (15, 150):
            for me in F.ORDER:
                r = F.get(R, t, n, M, me)
                print(t, n, M, me, "util %.3f" % st.mean([q[2] for x in r for q in x["resources"] if q[0] == "contact_util_mean"]),
                      "sec %.3f" % st.mean([st.mean(y["sec"] for y in x["rows"]) for x in r]))
        


if __name__ == "__main__":
    main()
