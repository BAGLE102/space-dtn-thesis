#!/usr/bin/env python3
"""由 performance.jsonl 畫簡報用的 matplotlib 圖。

用法：python3 make_ppt_figures.py results/performance.jsonl out_dir
"""
import collections
import json
import math
import os
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for name in ("DFKai-SB", "BiauKai", "AR PL UKai TW", "Noto Serif CJK TC", "Noto Sans CJK TC"):
    if any(f.name == name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 13, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#8A8A8A", "xtick.color": "#333333",
                     "ytick.color": "#555555", "axes.titlesize": 15})
COL = {"ours": "#5A50D0", "sr10": "#187A3E", "sr1": "#D97828"}
LAB = {"ours": "本方法", "sr10": "SR-CGR k=10", "sr1": "SR-CGR k=1"}
ORDER = ["ours", "sr10", "sr1"]
CELLS = [("random_20n", 100), ("random_20n", 300), ("random_40n", 100), ("random_40n", 300)]
XT = ["20 節點\nN=100", "20 節點\nN=300", "40 節點\nN=100", "40 節點\nN=300"]
T95 = 2.262  # 10 個 seed 的 t 值，df=9


def ci(xs):
    return T95 * st.stdev(xs) / math.sqrt(len(xs))


def load(path):
    R = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            R[(r["topology"], r["N"], r["M"], r["seed"], r["method"])] = r
    return R


def get(R, t, n, m, me):
    return [R[(t, n, m, s, me)] for s in range(1, 11)]


def delivery(r):
    return 100 * sum(x["arr"] is not None for x in r["rows"]) / len(r["rows"])


def grid(ax, axis="y"):
    ax.grid(axis=axis, color="#E4E4E4", lw=.8)
    ax.set_axisbelow(True)


def fig_delivery(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.35), sharey=True)
    w = .26
    summary = {}
    for ax, M in zip(axs, (3, 30)):
        for j, me in enumerate(ORDER):
            xs, ys, es = [], [], []
            for i, (t, n) in enumerate(CELLS):
                v = [delivery(r) for r in get(R, t, n, M, me)]
                xs.append(i + (j - 1) * w)
                ys.append(st.mean(v))
                es.append(ci(v))
                summary[(t, n, M, me)] = (st.mean(v), ci(v))
            ax.bar(xs, ys, w * .92, color=COL[me], label=LAB[me], yerr=es,
                   error_kw={"ecolor": "#333333", "elinewidth": 1, "capsize": 2.5})
            if M == 3:
                for x, y, e in zip(xs, ys, es):
                    ax.text(x, y + e + 1.5, "%.1f" % y, ha="center", va="bottom", fontsize=10.5, color="#222222")
        ax.set_xticks(range(4))
        ax.set_xticklabels(XT)
        ax.set_ylim(0, 112)
        ax.set_yticks(range(0, 101, 20))
        ax.set_title("Buffer = %d MB" % M, color="#222222")
        grid(ax)
    axs[0].set_ylabel("送達率（%）")
    axs[1].text(1.5, 106, "四組都是 99.3～100%", ha="center", va="center", fontsize=13, color="#222222")
    axs[0].legend(loc="lower center", ncol=3, frameon=True, framealpha=.95, edgecolor="none", fontsize=12.5,
                  bbox_to_anchor=(1.05, -.34))
    fig.subplots_adjust(left=.065, right=.995, top=.92, bottom=.24, wspace=.05)
    fig.savefig(os.path.join(out, "fig_delivery.png"), dpi=220)
    plt.close(fig)
    return summary


def paired(R, t, n, M, base):
    """每個 seed 內，兩邊都送達的包：本方法延遲 − 對照組延遲，取平均。"""
    res, cnt = [], 0
    for a, b in zip(get(R, t, n, M, "ours"), get(R, t, n, M, base)):
        d = [x["arr"] - y["arr"] for x, y in zip(a["rows"], b["rows"])
             if x["arr"] is not None and y["arr"] is not None]
        res.append(st.mean(d))
        cnt += len(d)
    return res, cnt


def fig_delay_time(R, out):
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.35))
    ax = axs[0]
    w = .3
    sm = {}
    for j, base in enumerate(("sr10", "sr1")):
        xs, ys, es = [], [], []
        for i, (t, n) in enumerate(CELLS):
            v, c = paired(R, t, n, 3, base)
            xs.append(i + (j - .5) * w)
            ys.append(st.mean(v))
            es.append(ci(v))
            sm[(t, n, 3, base, "delay")] = (st.mean(v), ci(v), c)
        ax.bar(xs, ys, w * .92, color=COL[base], label="對 " + LAB[base], yerr=es,
               error_kw={"ecolor": "#333333", "elinewidth": 1, "capsize": 2.5})
    ax.axhline(0, color="#555555", lw=1)
    ax.set_xticks(range(4))
    ax.set_xticklabels(XT)
    ax.set_ylabel("本方法 − 對照組（秒）")
    ax.set_title("延遲差（兩邊都送達的包，3 MB）", color="#222222")
    ax.text(.995, .03, "負值：本方法較快", transform=ax.transAxes, ha="right", fontsize=12, color="#555555")
    grid(ax)
    ax.legend(frameon=False, fontsize=12, loc="lower center", ncol=2, bbox_to_anchor=(.5, -.34))
    ax = axs[1]
    w = .26
    for j, me in enumerate(ORDER):
        xs, ys, es = [], [], []
        for i, (t, n) in enumerate(CELLS):
            v = [st.mean(x["sec"] for x in r["rows"]) for r in get(R, t, n, 3, me)]
            xs.append(i + (j - 1) * w)
            ys.append(st.mean(v))
            sm[(t, n, 3, me, "sec")] = st.mean(v)
        ax.bar(xs, ys, w * .92, color=COL[me], label=LAB[me], bottom=1e-3)
        for x, y in zip(xs, ys):
            ax.text(x, y * 1.12, ("%.3f" % y) if y < .1 else ("%.2f" % y), ha="center", va="bottom",
                    fontsize=10, color="#222222")
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 3)
    ax.set_yticks([1e-3, 1e-2, 1e-1, 1])
    ax.set_yticklabels(["0.001", "0.01", "0.1", "1"])
    ax.minorticks_off()
    ax.set_xticks(range(4))
    ax.set_xticklabels(XT)
    ax.set_ylabel("每包平均（秒，對數軸）")
    ax.set_title("計算時間（3 MB）", color="#222222")
    grid(ax)
    ax.legend(frameon=False, fontsize=12, loc="lower center", ncol=3, bbox_to_anchor=(.5, -.34))
    fig.subplots_adjust(left=.075, right=.995, top=.92, bottom=.24, wspace=.2)
    fig.savefig(os.path.join(out, "fig_delay_time.png"), dpi=220)
    plt.close(fig)
    return sm


def main():
    path, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    R = load(path)
    for k, v in sorted(fig_delivery(R, out).items()):
        print(k, "%.1f±%.1f" % v)
    for k, v in sorted(fig_delay_time(R, out).items(), key=str):
        print(k, v)
    wins = collections.Counter()
    for t, n in CELLS:
        for s in range(1, 11):
            o = delivery(R[(t, n, 3, s, "ours")])
            wins["both"] += o > delivery(R[(t, n, 3, s, "sr1")]) and o > delivery(R[(t, n, 3, s, "sr10")])
    print(wins)
    allsec = collections.defaultdict(list)
    for (t, n, M, s, me), r in R.items():
        allsec[(t, n, M, me)].append(st.mean(x["sec"] for x in r["rows"]))
    for me in ORDER:
        v = [st.mean(q) for k, q in allsec.items() if k[3] == me]
        print(me, "sec range all cells", round(min(v), 4), round(max(v), 4))


if __name__ == "__main__":
    main()
