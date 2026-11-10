"""Walker-delta contact plan 產生器（依 Alhajj & Corlay, arXiv:2410.15546v3 的星座設定）。

假設（論文未給或本實作簡化的部分）：
- 圓形 Kepler 軌道，不含攝動（J2、大氣阻力）；地球為半徑 6371 km 的球體。
- 衛星間：連線不穿過地球（最近點距地心 > R_E）即可通；論文的鏈路預算在此距離下必定通過（見 README）。
- 衛星—地面站：仰角 ≥ 0°。
- 地面站位置論文未給，預設 GS1 = 土魯斯、GS2 = 台北（可用參數更換）。
- 時間取樣 1 秒；contact = 連續可通的秒數；雙向各一條單向 contact。
- 傳播延遲 δ = 該 contact 期間平均距離 / 光速。
"""
import argparse, json, math
from datetime import datetime, timezone
import numpy as np

RE, MU, C = 6371.0, 398600.4418, 299792.458
WE = 7.2921159e-5

def gmst0(epoch):
    jd = epoch.timestamp() / 86400.0 + 2440587.5
    return math.radians((280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360)

def sat_positions(n_sat, n_planes, inc_deg, alt_km, t):
    r = RE + alt_km; n = math.sqrt(MU / r**3); i = math.radians(inc_deg)
    spp = n_sat // n_planes; P = []
    for p in range(n_planes):
        O = 2 * math.pi * p / n_planes
        for j in range(spp):
            u = 2 * math.pi * j / spp + n * t                      # zero phasing
            x = r * (math.cos(O) * np.cos(u) - math.sin(O) * np.sin(u) * math.cos(i))
            y = r * (math.sin(O) * np.cos(u) + math.cos(O) * np.sin(u) * math.cos(i))
            z = r * np.sin(u) * math.sin(i)
            P.append(np.stack([x, y, z], 1))
    return P

def gs_positions(lat, lon, t, g0):
    la, lo = math.radians(lat), math.radians(lon); th = g0 + WE * t + lo
    return np.stack([RE * math.cos(la) * np.cos(th), RE * math.cos(la) * np.sin(th), RE * math.sin(la) * np.ones_like(t)], 1)

def los(a, b):
    d = b - a; dd = np.einsum('ij,ij->i', d, d)
    s = np.clip(-np.einsum('ij,ij->i', a, d) / dd, 0, 1)
    q = a + d * s[:, None]
    return np.einsum('ij,ij->i', q, q) > RE**2

def elev_ok(g, s, min_el):
    d = s - g; up = g / np.linalg.norm(g, axis=1)[:, None]
    sin_el = np.einsum('ij,ij->i', d, up) / np.linalg.norm(d, axis=1)
    return sin_el >= math.sin(math.radians(min_el))

def runs(mask):
    m = np.concatenate([[False], mask, [False]]).astype(int); d = np.diff(m)
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))

def build(n_sat, n_planes=4, inc=52, alt=780, hours=24, gs=((43.60, 1.44), (25.03, 121.56)),
          min_el=0.0, epoch="2020-08-19T20:55:00"):
    T = int(hours * 3600); t = np.arange(T, dtype=float)
    g0 = gmst0(datetime.fromisoformat(epoch).replace(tzinfo=timezone.utc))
    S = sat_positions(n_sat, n_planes, inc, alt, t)
    G = [gs_positions(la, lo, t, g0) for la, lo in gs]
    names = ['S%d' % k for k in range(n_sat)] + ['GS%d' % (k + 1) for k in range(len(gs))]
    pos = S + G; out = []
    def add(u, v, mask):
        dist = np.linalg.norm(pos[u] - pos[v], axis=1)
        for a, b in runs(mask):
            dl = float(dist[a:b].mean() / C)
            out.append((names[u], names[v], int(a), int(b), dl)); out.append((names[v], names[u], int(a), int(b), dl))
    for u in range(n_sat):
        for v in range(u + 1, n_sat): add(u, v, los(S[u], S[v]))
        for k in range(len(gs)): add(n_sat + k, u, elev_ok(G[k], S[u], min_el))
    return names, out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sats", type=int, default=4); ap.add_argument("--out")
    a = ap.parse_args(); names, cp = build(a.sats)
    lens = [b - x for _, _, x, b, _ in cp]
    print("sats", a.sats, "unidirectional contacts", len(cp), "bidirectional", len(cp) // 2,
          "mean duration %.1f s" % (sum(lens) / len(lens)),
          "ISL", sum(1 for u, v, *_ in cp if u[0] == 'S' and v[0] == 'S') // 2,
          "GS", sum(1 for u, v, *_ in cp if 'GS' in u + v) // 2)
    if a.out: json.dump({"nodes": names, "contacts": cp}, open(a.out, "w"))
