// 區間 Label 候選方法的瀏覽器求解器（RELAX 模式）。與 src/experiments/interval_label_validation.py 對照。
const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
export class R {
  constructor(n, d = 1n) { if (d === 0n) throw new Error('除以 0'); if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; this.n = n / g; this.d = d / g; }
  static of(v) {
    if (v instanceof R) return v;
    if (typeof v === 'bigint') return new R(v);
    const s = String(v).trim();
    if (/^-?\d+\/\d+$/.test(s)) { const [a, b] = s.split('/'); return new R(BigInt(a), BigInt(b)); }
    if (/^-?\d+(\.\d+)?$/.test(s)) { const [a, b = ''] = s.split('.'); return new R(BigInt(a + b), 10n ** BigInt(b.length)); }
    throw new Error(`不是有效的數字：${s}`);
  }
  add(o) { o = R.of(o); return new R(this.n * o.d + o.n * this.d, this.d * o.d); }
  sub(o) { o = R.of(o); return new R(this.n * o.d - o.n * this.d, this.d * o.d); }
  mul(o) { o = R.of(o); return new R(this.n * o.n, this.d * o.d); }
  div(o) { o = R.of(o); return new R(this.n * o.d, this.d * o.n); }
  cmp(o) { o = R.of(o); const x = this.n * o.d - o.n * this.d; return x < 0n ? -1 : x > 0n ? 1 : 0; }
  lt(o) { return this.cmp(o) < 0; } le(o) { return this.cmp(o) <= 0; } gt(o) { return this.cmp(o) > 0; } ge(o) { return this.cmp(o) >= 0; } eq(o) { return this.cmp(o) === 0; }
  num() { return Number(this.n) / Number(this.d); }
  toString() { return this.d === 1n ? `${this.n}` : `${this.n}/${this.d}`; }
}
const ZERO = new R(0n);
const max = (...a) => a.reduce((x, y) => (x.ge(y) ? x : y));
const min = (...a) => a.reduce((x, y) => (x.le(y) ? x : y));
const uniqSort = (a) => { const s = [...a].sort((x, y) => x.cmp(y)); return s.filter((x, i) => i === 0 || !x.eq(s[i - 1])); };

export function parseInstance(raw) {
  const nodes = raw.nodes.map((n) => n.id);
  const P = { src: raw.src, dst: raw.dst, g: R.of(raw.g), S: R.of(raw.S), M: R.of(raw.M), T: R.of(raw.T), O: {}, cs: [] };
  const seen = new Set();
  for (const c of raw.contacts) {
    if (seen.has(c.id)) throw new Error(`Contact 編號重複：${c.id}`); seen.add(c.id);
    if (!nodes.includes(c.u) || !nodes.includes(c.v)) throw new Error(`${c.id} 的節點不存在`);
    if (c.u === c.v) throw new Error(`${c.id} 的傳送端與接收端相同`);
    const o = { id: c.id, u: c.u, v: c.v, a: R.of(c.a), b: R.of(c.b), r: R.of(c.r), d: R.of(c.d ?? 0), F: (c.F || []).map(([x, y]) => [R.of(x), R.of(y)]) };
    if (o.a.ge(o.b)) throw new Error(`${c.id} 的開始時間必須早於結束時間`);
    if (o.r.le(0)) throw new Error(`${c.id} 的速率必須大於 0`);
    if (o.d.lt(0)) throw new Error(`${c.id} 的延遲不可為負`);
    for (const [x, y] of o.F) if (x.ge(y)) throw new Error(`${c.id} 的預約時段不正確`);
    P.cs.push(o);
  }
  if (!nodes.includes(P.src) || !nodes.includes(P.dst)) throw new Error('來源或目的地不存在');
  if (P.src === P.dst) throw new Error('來源和目的地必須不同');
  if (P.S.le(0)) throw new Error('Bundle 大小必須大於 0');
  if (P.M.lt(P.S)) throw new Error('Buffer 上限必須不小於 Bundle 大小');
  for (const n of raw.nodes) {
    const cv = (n.bg || []).map(([t, v]) => [R.of(t), R.of(v)]);
    if (!cv.length) continue;
    if (n.id === P.src || n.id === P.dst) throw new Error('目前版本不測來源與目的地背景占用，請移除');
    for (let i = 1; i < cv.length; i++) if (cv[i][0].le(cv[i - 1][0])) throw new Error(`${n.id} 的背景時間必須遞增`);
    for (const [, v] of cv) if (v.lt(0)) throw new Error(`${n.id} 的背景占用不可為負`);
    P.O[n.id] = cv;
  }
  return P;
}
export function occ(cv, t) {
  if (!cv || !cv.length) return ZERO;
  if (t.le(cv[0][0])) return cv[0][1];
  for (let i = 1; i < cv.length; i++) if (t.le(cv[i][0])) { const [x0, y0] = cv[i - 1], [x1, y1] = cv[i]; return y0.add(y1.sub(y0).mul(t.sub(x0)).div(x1.sub(x0))); }
  return cv[cv.length - 1][1];
}
export function ramp(t, a, b, S) { if (t.le(a)) return ZERO; if (t.ge(b)) return S; return S.mul(t.sub(a)).div(b.sub(a)); }
export function visit(P, n, h, A, s, f) {
  const O = P.O[n] || []; const st = h === null ? A : h;
  const pts = [st, A, s, f, ...O.map((x) => x[0]).filter((x) => x.gt(st) && x.lt(f))];
  for (const t of pts) { if (t.lt(st)) continue; const rec = h === null ? P.S : ramp(t, h, A, P.S); if (occ(O, t).add(rec).sub(ramp(t, s, f, P.S)).gt(P.M)) return false; }
  return true;
}
const subtractOpen = (parts, x, y) => { const o = []; for (const [l, r] of parts) { if (r.le(x) || l.ge(y)) { o.push([l, r]); continue; } if (l.le(x)) o.push([l, x]); if (r.ge(y)) o.push([y, r]); } return o; };
export function startParts(P, c, head) {
  const d = P.S.div(c.r); const lo = max(c.a, head), hi = min(c.b.sub(d), P.T.sub(d).sub(c.d));
  if (lo.gt(hi)) return [];
  let p = [[lo, hi]]; for (const [x, y] of c.F) p = subtractOpen(p, x.sub(d), y); return p;
}
export function star(I1, U) { let v = null; for (const [l, r] of I1) if (l.le(U)) v = min(r, U); return v; }
export const upper = (P, c1, c2, s) => { const d1 = P.S.div(c1.r), d2 = P.S.div(c2.r); return s.sub(c1.d).sub(max(ZERO, d1.sub(d2))); };
export function feasibleAt(P, I1, c1, c2, s) {
  const k = star(I1, upper(P, c1, c2, s)); if (k === null) return { ok: false, s1: null };
  const d1 = P.S.div(c1.r), d2 = P.S.div(c2.r), h = k.add(c1.d);
  return { ok: visit(P, c1.v, h, h.add(d1), s, s.add(d2)), s1: k, h, A: h.add(d1), f: s.add(d2) };
}
export function bufferFilter(P, parts, I1, c1, c2) {
  const S = P.S, d1 = S.div(c1.r), d2 = S.div(c2.r), dl = c1.d, ex = max(ZERO, d1.sub(d2)), n = c1.v, O = P.O[n] || [], verts = O.map((x) => x[0]);
  const U = (s) => s.sub(dl).sub(ex); const feas = (s) => feasibleAt(P, I1, c1, c2, s).ok; const res = [];
  for (const [lo, hi] of parts) {
    if (lo.eq(hi)) { if (feas(lo)) res.push([lo, hi]); continue; }
    let cr = [lo, hi]; for (const [l, r] of I1) cr.push(l.add(dl).add(ex), r.add(dl).add(ex));
    cr = uniqSort(cr.filter((x) => x.ge(lo) && x.le(hi))); let pts = [...cr];
    for (let i = 0; i + 1 < cr.length; i++) {
      const p = cr[i], q = cr[i + 1], a = p.add(q.sub(p).div(3)), b = p.add(q.sub(p).mul(2).div(3)), ka = star(I1, U(a)), kb = star(I1, U(b));
      if (ka === null || kb === null) continue;
      const al = kb.sub(ka).div(b.sub(a)), be = ka.sub(al.mul(a)), one = new R(1n);
      const mv = [[al, be.add(dl)], [al, be.add(dl).add(d1)], [one, ZERO], [one, d2]]; let sub = [p, q];
      mv.forEach(([a1, b1], j) => {
        for (const x of verts) if (a1.cmp(0) !== 0) { const z = x.sub(b1).div(a1); if (z.gt(p) && z.lt(q)) sub.push(z); }
        for (const [a2, b2] of mv.slice(j + 1)) if (!a1.eq(a2)) { const z = b2.sub(b1).div(a1.sub(a2)); if (z.gt(p) && z.lt(q)) sub.push(z); }
      });
      sub = uniqSort(sub); pts.push(...sub);
      for (let w = 0; w + 1 < sub.length; w++) {
        const u = sub[w], v = sub[w + 1], e = u.add(v.sub(u).div(3)), g = u.add(v.sub(u).mul(2).div(3)), m = u.add(v).div(2), km = al.mul(m).add(be), lt = km.add(dl), ht = m.add(d2);
        const occs = (s) => { const k = al.mul(s).add(be), h = k.add(dl), A = h.add(d1), f = s.add(d2); return [h, A, s, f, ...verts.filter((x) => x.gt(lt) && x.lt(ht))].map((t) => occ(O, t).add(ramp(t, h, A, S)).sub(ramp(t, s, f, S)).sub(P.M)); };
        const fa = occs(e), fb = occs(g);
        fa.forEach((x, idx) => { if (!x.eq(fb[idx])) { const z = e.sub(x.mul(g.sub(e)).div(fb[idx].sub(x))); if (z.gt(u) && z.lt(v)) pts.push(z); } });
      }
    }
    pts = uniqSort(pts); let cur = null;
    pts.forEach((p, i) => {
      const ok = feas(p);
      if (ok) { if (!cur) cur = [p, p]; else cur[1] = p; } else if (cur) { res.push(cur); cur = null; }
      if (i + 1 < pts.length) { const m = p.add(pts[i + 1]).div(2); if (feas(m)) { if (!cur) cur = [ok ? p : m, ok ? p : m]; cur[1] = m; } else if (cur) { res.push(cur); cur = null; } }
    });
    if (cur) res.push(cur);
  }
  return merge(res);
}
export function merge(p) { const s = [...p].sort((a, b) => a[0].cmp(b[0])), o = []; for (const [l, r] of s) { if (o.length && l.le(o[o.length - 1][1])) o[o.length - 1][1] = max(o[o.length - 1][1], r); else o.push([l, r]); } return o; }
export function minus(parts, done) {
  for (const [l, r] of done) { const n = []; for (const [a, b] of parts) { if (b.lt(l) || a.gt(r)) { n.push([a, b]); continue; } if (a.lt(l)) n.push([a, l]); if (b.gt(r)) n.push([r, b]); } parts = n; }
  return parts.filter(([a, b]) => a.lt(b) || !done.some(([l, r]) => l.le(a) && a.le(r)));
}
export function backtrack(P, goal, byId) {
  let l = goal, s = l.I[0], out = [{ c: l.c, s }];
  while (l.pred !== null) { const q = byId[l.pred], k = star([q.I], upper(P, q.c, l.c, s)); out.unshift({ c: q.c, s: k }); l = q; s = k; }
  return out;
}
export function replay(P, sch) {
  if (!sch.length || sch[0].c.u !== P.src || sch[sch.length - 1].c.v !== P.dst) return false;
  let prev = null, n = P.src;
  for (const { c, s } of sch) {
    const d = P.S.div(c.r), f = s.add(d); if (c.u !== n || s.lt(c.a) || f.gt(c.b) || f.add(c.d).gt(P.T)) return false;
    if (c.F.some(([x, y]) => s.lt(y) && x.lt(f))) return false;
    let h = null, A = P.g;
    if (!prev) { if (s.lt(P.g)) return false; } else { h = prev.s.add(prev.c.d); A = h.add(P.S.div(prev.c.r)); if (s.lt(h) || f.lt(A)) return false; }
    if (!visit(P, n, h, A, s, f)) return false; prev = { c, s }; n = c.v;
  }
  return true;
}
export function selfOverlap(P, sch) { const last = {}; for (const { c, s } of sch) { const f = s.add(P.S.div(c.r)), h = s.add(c.d); last[c.u] = f; if (last[c.v] && h.lt(last[c.v])) return true; } return false; }

export function solve(P, onEvent = () => {}, limit = 5000) {
  const out = {}; for (const c of P.cs) (out[c.u] ||= []).push(c);
  const labels = [], Q = [], reached = Object.fromEntries(P.cs.map((c) => [c.id, []])); let tick = 0;
  const qsort = () => Q.sort((a, b) => a.key.cmp(b.key) || a.tick - b.tick);
  const insert = (c, parts, pred) => { const nw = minus(parts, reached[c.id]); reached[c.id] = merge([...reached[c.id], ...nw]); const made = []; for (const I of nw) { const l = { id: labels.length, c, I, pred, key: I[0].add(P.S.div(c.r)).add(c.d), tick: tick++, st: 'queue' }; labels.push(l); Q.push(l); made.push(l); } qsort(); return { nw, made }; };
  const ctx = () => ({ labels, Q, reached });
  onEvent('init', ctx(), {});
  for (const c of out[P.src] || []) { const parts = startParts(P, c, P.g); onEvent('source', ctx(), { c, parts }); const { nw, made } = insert(c, parts, null); onEvent('insert', ctx(), { c, parts, nw, made, pred: null }); }
  let goal = null, status = 'NO_PATH';
  while (Q.length) {
    if (labels.length > limit) { status = 'UNKNOWN'; break; }
    const L1 = Q.shift(); L1.st = 'current'; onEvent('pop', ctx(), { L1 });
    if (L1.c.v === P.dst) { L1.st = 'goal'; goal = L1; status = 'FOUND'; onEvent('goal', ctx(), { L1 }); break; }
    const c1 = L1.c, d1 = P.S.div(c1.r);
    const nxt = out[c1.v] || []; if (!nxt.length) onEvent('dead', ctx(), { L1 });
    for (const c2 of nxt) {
      const d2 = P.S.div(c2.r), head = L1.I[0].add(c1.d).add(max(ZERO, d1.sub(d2))); const parts = startParts(P, c2, head);
      onEvent('range', ctx(), { L1, c2, parts, head });
      const res = bufferFilter(P, parts, [L1.I], c1, c2); onEvent('filter', ctx(), { L1, c2, parts, res });
      const { nw, made } = insert(c2, res, L1.id); onEvent('insert', ctx(), { L1, c: c2, parts: res, nw, made, pred: L1.id });
    }
    L1.st = 'done';
  }
  let sch = null, valid = null, overlap = null;
  if (goal) { sch = backtrack(P, goal, labels); valid = replay(P, sch); overlap = selfOverlap(P, sch); }
  onEvent('finish', ctx(), { goal, sch, valid, overlap, status });
  return { goal, sch, valid, overlap, status, labels, reached };
}
