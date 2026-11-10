"""Iridium 星座 contact plan（依 ns-2 內建 Iridium 模型的設計參數）。

參數（ns-2 文件 17.1.2）：6 面 × 11 顆、高度 780 km、傾角 86.4°、相鄰面間隔 31.6°、接縫 22°、
每顆 4 條 ISL（同面前後 2 條常通；相鄰同向面左右 2 條，任一端緯度 > 60° 時關閉；接縫兩側不連）、
地面仰角門檻 8.2°、ISL 25 Mb/s、上下行 1.5 Mb/s。
假設：圓形 Kepler 軌道、球形地球；相鄰面衛星相位錯開半個間距（星座常見交錯）；
相鄰面 ISL 連到同編號衛星；地面站預設 GS1 土魯斯、GS2 台北。
"""
import json, math, argparse
import numpy as np
from walker_cp import RE, MU, C, gmst0, gs_positions, elev_ok, runs
from datetime import datetime, timezone

def build(hours=24, gs=((43.60, 1.44), (25.03, 121.56)), epoch="2020-08-19T20:55:00",
          planes=6, spp=11, alt=780, inc=86.4, dO=31.6, lat_th=60, min_el=8.2):
    T = int(hours * 3600); t = np.arange(T, dtype=float)
    r = RE + alt; n = math.sqrt(MU / r**3); i = math.radians(inc)
    S, LAT, idx = [], [], {}
    for p in range(planes):
        O = math.radians(dO * p)
        for j in range(spp):
            u = 2 * math.pi * j / spp + (math.pi / spp) * (p % 2) + n * t
            x = r * (math.cos(O) * np.cos(u) - math.sin(O) * np.sin(u) * math.cos(i))
            y = r * (math.sin(O) * np.cos(u) + math.cos(O) * np.sin(u) * math.cos(i))
            z = r * np.sin(u) * math.sin(i)
            idx[(p, j)] = len(S); S.append(np.stack([x, y, z], 1)); LAT.append(np.degrees(np.arcsin(z / r)))
    g0 = gmst0(datetime.fromisoformat(epoch).replace(tzinfo=timezone.utc))
    G = [gs_positions(la, lo, t, g0) for la, lo in gs]
    names = ['P%dS%d' % (p, j) for p in range(planes) for j in range(spp)] + ['GS%d' % (k + 1) for k in range(len(gs))]
    pos = S + G; out = []; kind = {}
    def add(u, v, mask, k):
        dist = np.linalg.norm(pos[u] - pos[v], axis=1)
        for a, b in runs(mask):
            dl = float(dist[a:b].mean() / C)
            for x, y in ((u, v), (v, u)): out.append((names[x], names[y], int(a), int(b), dl, k))
    for p in range(planes):
        for j in range(spp):
            a = idx[(p, j)]
            add(a, idx[(p, (j + 1) % spp)], np.ones(T, bool), 'intra')
            if p + 1 < planes:
                b = idx[(p + 1, j)]
                add(a, b, (np.abs(LAT[a]) <= lat_th) & (np.abs(LAT[b]) <= lat_th), 'inter')
    for k in range(len(gs)):
        for a in range(len(S)): add(len(S) + k, a, elev_ok(G[k], S[a], min_el), 'gsl')
    return names, out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out"); a = ap.parse_args()
    names, cp = build()
    for k in ('intra', 'inter', 'gsl'):
        L = [c[3] - c[2] for c in cp if c[5] == k]
        print(k, 'unidirectional', len(L), 'mean %.0f s' % (sum(L) / len(L)))
    if a.out: json.dump({"nodes": names, "contacts": [c[:5] for c in cp], "kind": [c[5] for c in cp]}, open(a.out, "w"))
