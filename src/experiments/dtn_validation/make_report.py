#!/usr/bin/env python3
"""由結果檔產生 Excel 與圖片。不重新跑實驗。"""
import argparse
import collections
import datetime
import json
import math
import os
import platform
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLOR = {"ours": "#2a78d6", "sr1": "#eb6834", "sr10": "#1baf7a"}
LABEL = {"ours": "Proposed", "sr1": "SR-CGR (k=1)", "sr10": "SR-CGR (k=10)"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26,
       10: 2.23, 11: 2.20, 12: 2.18, 13: 2.16, 14: 2.14, 15: 2.13, 19: 2.09, 29: 2.05}
MIN_SEEDS_FOR_CI = 5


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def ci95(xs):
    if len(xs) < 2:
        return 0.0
    df = len(xs) - 1
    t = T95.get(df) or T95[max(k for k in T95 if k <= df)]
    return t * st.stdev(xs) / math.sqrt(len(xs))


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def group(runs):
    """{(topology, N, M): {seed: {method: run}}}"""
    g = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in runs:
        g[(r["topology"], r["N"], r["M"])][r["seed"]][r["method"]] = r
    return g


def common_n(by_method):
    return min(len(r["rows"]) for r in by_method.values())


def delays(row):
    return row["arr"] - row["g"] if row["arr"] is not None else None


# ---------- Excel ----------
def sheet(wb, title, headers, rows, widths=None, note=None):
    ws = wb.create_sheet(title)
    r0 = 1
    if note:
        ws.cell(1, 1, note).font = Font(name="Arial", italic=True, color="52514E")
        r0 = 3
    for j, h in enumerate(headers, 1):
        c = ws.cell(r0, j, h)
        c.font = Font(name="Arial", bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="44546A")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    font = Font(name="Arial")
    for i, row in enumerate(rows, r0 + 1):
        for j, v in enumerate(row, 1):
            c = ws.cell(i, j, v(i) if callable(v) else v)
            c.font = font
            if isinstance(v, float):
                c.number_format = "0.000" if abs(v) < 100 else "0.0"
    for j, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(j)].width = (widths or {}).get(h, max(11, min(24, len(h) + 3)))
    ws.freeze_panes = ws.cell(r0 + 1, 1)
    if rows:
        ws.auto_filter.ref = "A%d:%s%d" % (r0, get_column_letter(len(headers)), r0 + len(rows))
    return ws


def summary_rows(g, cfg):
    rows = []
    for (t, n, m), seeds in sorted(g.items()):
        methods = sorted({me for d in seeds.values() for me in d})
        for me in methods:
            rs = [d[me] for d in seeds.values() if me in d]
            all_rows = [x for r in rs for x in r["rows"]]
            ds = [delays(x) for x in all_rows if x["arr"] is not None]
            hops = [x["hops"] for x in all_rows if x["arr"] is not None]
            secs = [x["sec"] for x in all_rows]
            planned, done, ok = n * len(rs), len(all_rows), len(ds)
            rows.append([t, n, m, LABEL[me], len(rs), planned, done, ok,
                         lambda i: "=IF(G%d=0,\"\",H%d/G%d)" % (i, i, i),
                         st.mean(ds) if ds else None, st.median(ds) if ds else None, pct(ds, .95),
                         st.mean(hops) if hops else None, st.mean(secs) if secs else None,
                         "yes" if done == planned else "no",
                         sum(x["why"] == "VALIDATION_FAILED" for x in all_rows)])
    return rows


def pair_rows(g):
    rows = []
    for (t, n, m), seeds in sorted(g.items()):
        for base in ("sr1", "sr10"):
            shared = both = early = same = late = 0
            sum_o = sum_b = 0.0
            win = tie = loss = 0
            for d in seeds.values():
                if "ours" not in d or base not in d:
                    continue
                k = min(len(d["ours"]["rows"]), len(d[base]["rows"]))
                shared += k
                do = db = 0
                for x, y in zip(d["ours"]["rows"][:k], d[base]["rows"][:k]):
                    do += x["arr"] is not None
                    db += y["arr"] is not None
                    if x["arr"] is not None and y["arr"] is not None:
                        p, q = delays(x), delays(y)
                        both += 1
                        sum_o += p
                        sum_b += q
                        early += p < q - 1e-9
                        late += p > q + 1e-9
                        same += abs(p - q) <= 1e-9
                win += do > db
                tie += do == db
                loss += do < db
            rows.append([t, n, m, LABEL[base], shared, both,
                         sum_o / both if both else None, sum_b / both if both else None,
                         lambda i: "=IF(F%d=0,\"\",G%d-H%d)" % (i, i, i),
                         lambda i: "=IF(F%d=0,\"\",(G%d-H%d)/H%d)" % (i, i, i, i),
                         early, same, late, win, tie, loss])
    return rows


def build_excel(path, runs, val, cfg):
    wb = Workbook()
    wb.remove(wb.active)
    g = group(runs)
    s = sheet(wb, "Summary",
              ["Topology", "N", "Buffer (MB)", "Method", "Seeds", "Planned bundles", "Processed bundles",
               "Delivered", "Delivery ratio", "Mean delay (s)", "Median delay (s)", "P95 delay (s)",
               "Mean hops", "Mean compute (s/bundle)", "Complete", "Validation failures"],
              summary_rows(g, cfg), widths={"Method": 16},
              note="Delay here covers each method's own delivered bundles. Use Pairwise to compare delay across methods.")
    for row in s.iter_rows(min_row=4, min_col=9, max_col=9):
        row[0].number_format = "0.0%"
    p = sheet(wb, "Pairwise",
              ["Topology", "N", "Buffer (MB)", "Proposed vs", "Shared bundles", "Both delivered",
               "Proposed delay (s)", "Baseline delay (s)", "Delay diff (s)", "Delay diff (%)",
               "Earlier", "Same", "Later", "Seeds won", "Seeds tied", "Seeds lost"],
              pair_rows(g), widths={"Proposed vs": 16},
              note="Only bundles both methods processed. Negative delay diff means the proposed method is faster.")
    for row in p.iter_rows(min_row=4, min_col=10, max_col=10):
        row[0].number_format = "0.00%"
    bundles = []
    for r in runs:
        for x in r["rows"]:
            bundles.append([r["topology"], r["N"], r["M"], r["seed"], LABEL[r["method"]], x["i"], x["src"], x["dst"],
                            x["g"], "yes" if x["arr"] is not None else "no", x["arr"], delays(x), x["hops"],
                            x["path"], x["starts"], x["sec"], x["why"]])
    sheet(wb, "Bundles", ["Topology", "N", "Buffer (MB)", "Seed", "Method", "Bundle", "Source", "Destination",
                          "g (s)", "Delivered", "Arrival (s)", "Delay (s)", "Hops", "Path",
                          "Contact@start", "Compute (s)", "Reason"], bundles,
          widths={"Path": 22, "Contact@start": 40, "Method": 16, "Reason": 18})
    sheet(wb, "Oracle", ["Case", "Bundle", "Source", "Destination", "g (s)", "Proposed arrival (s)",
                         "Oracle arrival (s)", "Difference (s)", "Result", "Replay OK", "Proposed (s)", "Oracle (s)"],
          [[v["case"], v["bundle"], v["src"], v["dst"], v["g"], v["ours"], v["oracle"],
            lambda i: "=IF(OR(F%d=\"\",G%d=\"\"),\"\",F%d-G%d)" % (i, i, i, i),
            v["result"], v["replay_ok"], v["ours_sec"], v["oracle_sec"]] for v in val])
    count = collections.Counter(v["result"] for v in val)
    labels = [("same", "Both feasible, same arrival"), ("both_none", "Both infeasible"),
              ("later", "Proposed later than oracle"), ("earlier", "Proposed earlier (between grid points)"),
              ("missed", "Proposed missed a solution"), ("extra", "Proposed found, oracle none")]
    last = len(labels) + 1
    os_rows = [[lab, count.get(k, 0)] for k, lab in labels]
    os_rows.append(["Replay failures", sum(v["replay_ok"] is False for v in val)])
    os_rows.append(["Total queries", lambda i: "=SUM(B2:B%d)" % last])
    sheet(wb, "Oracle_Summary", ["Item", "Queries"], os_rows, widths={"Item": 42})
    res = []
    for r in runs:
        for kind, item, val_, when in r["resources"]:
            over = "yes" if kind == "node_peak_mb" and val_ > r["M"] + 1e-9 else ""
            res.append([r["topology"], r["N"], r["M"], r["seed"], LABEL[r["method"]], kind, item, val_, when, over])
    sheet(wb, "Resources", ["Topology", "N", "Buffer (MB)", "Seed", "Method", "Metric", "Item", "Value",
                            "Time (s)", "Over limit"], res, widths={"Metric": 20, "Method": 16})
    conf = [["Created", datetime.datetime.now().isoformat(timespec="seconds")],
            ["Python", platform.python_version()], ["Platform", platform.platform()],
            ["CPU", platform.processor()], ["Time unit", "second"], ["Data unit", "MB (decimal)"],
            ["Destination model", "A bundle leaves the destination the moment it is fully received."],
            ["Source model", "A bundle occupies the source from g until it is sent."],
            ["Baseline", "Simplified SR-CGR from the definition; not a full CGR implementation."],
            ["Oracle", "Grid enumeration per bundle; earlier bundles fixed; not a global optimum."],
            ["Config", json.dumps(cfg, ensure_ascii=False)]]
    shas = sorted({(r["topology"], r["seed"], r["contact_sha256"]) for r in runs})
    conf += [["Contact SHA-256 %s seed %s" % (t, s_), h] for t, s_, h in shas]
    ws = sheet(wb, "Config", ["Item", "Value"], conf, widths={"Item": 36, "Value": 90})
    wb.save(path)


# ---------- Figures ----------
def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=.8)
    ax.set_axisbelow(True)


def save(fig, out, name):
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(out, "%s.%s" % (name, ext)), dpi=200, facecolor="white")
    plt.close(fig)


def ratio(r):
    rows = r["rows"]
    return sum(x["arr"] is not None for x in rows) / len(rows) if rows else None


def plot_ratio(ax, g, topo, keyf, xs, fixed, x_is_buffer, seeds_note=True):
    methods = sorted({r for k, s in g.items() if k[0] == topo for d in s.values() for r in d},
                     key=list(COLOR).index)
    width = (max(xs) - min(xs) or 1)
    for me in methods:
        px, py, pe, raw = [], [], [], []
        for x in xs:
            key = (topo, fixed, x) if x_is_buffer else (topo, x, fixed)
            vals = [ratio(d[me]) * 100 for d in g.get(key, {}).values() if me in d and ratio(d[me]) is not None]
            if vals:
                px.append(x)
                py.append(st.mean(vals))
                pe.append(ci95(vals) if len(vals) >= MIN_SEEDS_FOR_CI else 0)
                raw.append(vals)
        ax.errorbar(px, py, yerr=pe, color=COLOR[me], marker="o", markersize=7, linewidth=2,
                    capsize=3, label=LABEL[me])
        if any(len(v) < MIN_SEEDS_FOR_CI for v in raw):
            for x, v in zip(px, raw):
                ax.scatter([x] * len(v), v, color=COLOR[me], s=12, alpha=.35)
    ax.set_ylim(0, 105)
    ax.set_xticks(xs)
    ax.set_ylabel("Delivery ratio (%)", color=MUTED, fontsize=9)
    style(ax)


def figures(out, runs, val):
    os.makedirs(out, exist_ok=True)
    g = group(runs)
    topos = sorted({k[0] for k in g})
    for t in topos:
        Ns = sorted({k[1] for k in g if k[0] == t})
        Ms = sorted({k[2] for k in g if k[0] == t})
        fig, axs = plt.subplots(1, len(Ns), figsize=(4.2 * len(Ns), 3.6), squeeze=False, sharey=True)
        for ax, n in zip(axs[0], Ns):
            plot_ratio(ax, g, t, None, Ms, n, True)
            ax.set_title("N = %d" % n, fontsize=10, color=INK, loc="left")
            ax.set_xlabel("Node buffer (MB)", color=MUTED, fontsize=9)
        axs[0][0].legend(frameon=False, fontsize=8, loc="lower right")
        fig.suptitle("%s: delivery ratio by buffer" % t, fontsize=11, color=INK, x=.02, ha="left")
        save(fig, out, "fig1_delivery_vs_buffer_%s" % t)

        fig, axs = plt.subplots(1, len(Ms), figsize=(4.2 * len(Ms), 3.6), squeeze=False, sharey=True)
        for ax, m in zip(axs[0], Ms):
            plot_ratio(ax, g, t, None, Ns, m, False)
            ax.set_title("Buffer = %s MB" % m, fontsize=10, color=INK, loc="left")
            ax.set_xlabel("Bundles (N)", color=MUTED, fontsize=9)
        axs[0][0].legend(frameon=False, fontsize=8, loc="lower left")
        fig.suptitle("%s: delivery ratio by load" % t, fontsize=11, color=INK, x=.02, ha="left")
        save(fig, out, "fig2_delivery_vs_load_%s" % t)

        keys = sorted(k for k in g if k[0] == t)
        fig, ax = plt.subplots(figsize=(1.5 * len(keys) + 2, 3.6))
        for mi, me in enumerate(("ours", "sr1", "sr10")):
            xs, ys, es = [], [], []
            for i, k in enumerate(keys):
                per_seed = []
                for d in g[k].values():
                    if not all(x in d for x in COLOR):
                        continue
                    c = common_n(d)
                    ds = [delays(d[me]["rows"][j]) for j in range(c)
                          if all(d[x]["rows"][j]["arr"] is not None for x in COLOR)]
                    if ds:
                        per_seed.append(st.mean(ds))
                if per_seed:
                    xs.append(i + (mi - 1) * .22)
                    ys.append(st.mean(per_seed))
                    es.append(ci95(per_seed) if len(per_seed) >= MIN_SEEDS_FOR_CI else 0)
            ax.errorbar(xs, ys, yerr=es, fmt="o", color=COLOR[me], markersize=7, capsize=3, label=LABEL[me])
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(["N=%d\n%s MB" % (k[1], k[2]) for k in keys])
        ax.set_ylabel("Mean delay (s)", color=MUTED, fontsize=9)
        ax.set_title("%s: delay on bundles all methods delivered" % t, fontsize=11, color=INK, loc="left")
        ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.18))
        style(ax)
        save(fig, out, "fig3_common_delay_%s" % t)

        fig, axs = plt.subplots(1, len(Ms), figsize=(4.2 * len(Ms), 3.4), squeeze=False)
        for ax, m in zip(axs[0], Ms):
            diff = []
            for n in Ns:
                for d in g.get((t, n, m), {}).values():
                    if "ours" in d and "sr10" in d:
                        k = min(len(d["ours"]["rows"]), len(d["sr10"]["rows"]))
                        for x, y in zip(d["ours"]["rows"][:k], d["sr10"]["rows"][:k]):
                            if x["arr"] is not None and y["arr"] is not None:
                                diff.append(delays(x) - delays(y))
            faster = [x for x in diff if x < -1e-9]
            slower = [x for x in diff if x > 1e-9]
            same = len(diff) - len(faster) - len(slower)
            if faster or slower:
                both = faster + slower
                lim = max(abs(pct(both, .01)), abs(pct(both, .99))) or 1
                bins = [-lim + 2 * lim * i / 40 for i in range(41)]
                ax.hist([max(-lim, min(lim, x)) for x in faster], bins=bins, color=COLOR["ours"], label="Proposed faster")
                ax.hist([max(-lim, min(lim, x)) for x in slower], bins=bins, color=COLOR["sr1"], label="Proposed slower")
                ax.legend(frameon=False, fontsize=8)
            ax.axvline(0, color=MUTED, linewidth=.8)
            ax.set_title("Buffer = %s MB (%d faster, %d equal, %d slower)" % (m, len(faster), same, len(slower)),
                         fontsize=9, color=INK, loc="left")
            ax.set_xlabel("Delay difference vs SR-CGR k=10 (s)", color=MUTED, fontsize=9)
            ax.set_ylabel("Bundles", color=MUTED, fontsize=9)
            style(ax)
        save(fig, out, "fig4_delay_difference_%s" % t)

        fig, ax = plt.subplots(figsize=(5.5, 3.4))
        data, labels, colors = [], [], []
        for me in COLOR:
            secs = [x["sec"] for r in runs if r["topology"] == t and r["method"] == me for x in r["rows"] if x["sec"] > 0]
            if secs:
                data.append(secs)
                labels.append(LABEL[me])
                colors.append(COLOR[me])
        box = ax.boxplot(data, vert=False, patch_artist=True, showfliers=False, widths=.5)
        ax.set_yticklabels(labels)
        for b, c in zip(box["boxes"], colors):
            b.set(facecolor=c, edgecolor=c, alpha=.75)
        for m_ in box["medians"]:
            m_.set_color(INK)
        ax.set_xscale("log")
        ax.set_xlabel("Compute time per bundle (s, log scale; outliers hidden)", color=MUTED, fontsize=9)
        ax.set_title("%s: compute time" % t, fontsize=11, color=INK, loc="left")
        style(ax)
        ax.grid(axis="x", color=GRID, linewidth=.8)
        ax.grid(axis="y", visible=False)
        save(fig, out, "fig5_compute_time_%s" % t)
    if val:
        count = collections.Counter(v["result"] for v in val)
        items = [("same", "Same arrival"), ("both_none", "Both infeasible"), ("earlier", "Proposed earlier"),
                 ("later", "Proposed later"), ("missed", "Proposed missed"), ("extra", "Oracle none")]
        fig, ax = plt.subplots(figsize=(6.5, 3))
        names = [b for _, b in items][::-1]
        vals = [count.get(a, 0) for a, _ in items][::-1]
        ax.barh(names, vals, color=COLOR["ours"], height=.55)
        for i, v in enumerate(vals):
            ax.text(v, i, " %d" % v, va="center", color=INK, fontsize=9)
        ax.set_xlabel("Queries", color=MUTED, fontsize=9)
        ax.set_title("Proposed method vs grid oracle (%d queries)" % len(val), fontsize=11, color=INK, loc="left")
        style(ax)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID, linewidth=.8)
        save(fig, out, "fig6_oracle_agreement")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--config", default="config.json")
    a = ap.parse_args()
    runs = load(os.path.join(a.results, "performance.jsonl"))
    val = load(os.path.join(a.results, "validation.jsonl"))
    cfg = json.load(open(a.config, encoding="utf-8"))
    build_excel(os.path.join(a.results, "report.xlsx"), runs, val, cfg)
    figures(os.path.join(a.results, "figures"), runs, val)
    print("runs:", len(runs), "validation queries:", len(val))
    print("wrote", os.path.join(a.results, "report.xlsx"), "and", os.path.join(a.results, "figures"))


if __name__ == "__main__":
    main()
