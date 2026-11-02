import { R, parseInstance, solve, feasibleAt, occ, ramp, star, upper } from './solver.mjs';
const $ = (s) => document.querySelector(s);
const el = (t, a = {}, ...kids) => { const e = document.createElement(t); for (const [k, v] of Object.entries(a)) { if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v; else e.setAttribute(k, v); } kids.forEach((x) => e.append(x)); return e; };
const NS = 'http://www.w3.org/2000/svg';
const sv = (t, a = {}, txt) => { const e = document.createElementNS(NS, t); for (const [k, v] of Object.entries(a)) e.setAttribute(k, v); if (txt !== undefined) e.textContent = txt; return e; };
const bump = (t, h = 10, rise = 1, hold = 1) => [[t, 0], [t + rise, h], [t + rise + hold, h], [t + 2 * rise + hold, 0]];
const fmt = (ps) => (ps && ps.length ? ps.map(([a, b]) => (a.eq(b) ? `{${a}}` : `[${a}, ${b}]`)).join(' ∪ ') : '空');
const c0 = (id, u, v, a, b, r, d = 0, F = []) => ({ id, u, v, a, b, r, d, F });
const CASES = [
  { name: '基本：下一跳第 2 秒才開（7 秒）', src: 'A', dst: 'C', g: 0, S: 10, M: 10, T: 40, nodes: [{ id: 'A', x: 90, y: 180 }, { id: 'B', x: 320, y: 180 }, { id: 'C', x: 550, y: 180 }], contacts: [c0('c1', 'A', 'B', 0, 10, 2), c0('c2', 'B', 'C', 2, 12, 2)] },
  { name: 'Buffer：B 只剩 3 MB', src: 'A', dst: 'C', g: 0, S: 10, M: 10, T: 40, nodes: [{ id: 'A', x: 90, y: 180 }, { id: 'B', x: 320, y: 180, bg: [[0, 7], [40, 7]] }, { id: 'C', x: 550, y: 180 }], contacts: [c0('c1', 'A', 'B', 0, 10, 2), c0('c2', 'B', 'C', 2, 12, 2)] },
  { name: '一條 Contact 兩個 Label', src: 'A', dst: 'D', g: 0, S: 10, M: 10, T: 40, nodes: [{ id: 'A', x: 70, y: 180 }, { id: 'B', x: 240, y: 180 }, { id: 'C', x: 410, y: 180, bg: bump(11) }, { id: 'D', x: 580, y: 180 }], contacts: [c0('c1', 'A', 'B', 0, 10, 2), c0('c2', 'B', 'C', 2, 20, 2, 0, [[9, 10]]), c0('c3', 'C', 'D', 16, 21, 2)] },
  { name: '完整拓譜：繞路最早（20 秒）', src: 'A', dst: 'D', g: 0, S: 10, M: 10, T: 40, nodes: [{ id: 'A', x: 60, y: 180 }, { id: 'B', x: 240, y: 60, bg: bump(11) }, { id: 'V', x: 240, y: 200 }, { id: 'E', x: 400, y: 50, bg: bump(11) }, { id: 'C', x: 300, y: 285, bg: bump(5) }, { id: 'F', x: 130, y: 320 }, { id: 'D', x: 580, y: 180 }], contacts: [c0('c1', 'A', 'B', 0, 10, 2), c0('c2', 'A', 'C', 1, 8, 2, 1), c0('c3', 'B', 'E', 2, 20, 2, 0, [[9, 10]]), c0('c4', 'E', 'D', 16, 21, 2), c0('c5', 'B', 'V', 3, 9, 2), c0('c6', 'V', 'B', 15, 20, 2), c0('c7', 'B', 'D', 18, 21, 5), c0('c8', 'C', 'D', 9, 11, 5), c0('c9', 'A', 'F', 0, 6, 2), c0('c10', 'F', 'D', 20, 30, 1)] },
  { name: '原 PPT 第二包（3 秒）', src: 'A', dst: 'D', g: 1, S: 4, M: 4, T: 16, nodes: [{ id: 'A', x: 90, y: 270 }, { id: 'B', x: 320, y: 80, bg: [[2, 0], [3, 4], [6, 4], [7, 0]] }, { id: 'C', x: 320, y: 280 }, { id: 'D', x: 550, y: 180 }], contacts: [c0('c3', 'A', 'B', 1, 2, 4), c0('c4', 'A', 'B', 7, 9, 4), c0('c5', 'B', 'D', 10, 11, 4, 1), c0('c6', 'A', 'C', 1, 2, 4, 1), c0('c8', 'C', 'D', 2, 3, 4)] },
  { name: '滿載節點只能同步穿過', src: 'S', dst: 'T', g: 0, S: 4, M: 4, T: 30, nodes: [{ id: 'S', x: 90, y: 180 }, { id: 'V', x: 320, y: 180, bg: [[0, 4], [20, 4]] }, { id: 'T', x: 550, y: 180 }], contacts: [c0('in', 'S', 'V', 2, 3, 4), c0('out', 'V', 'T', 2, 3, 4)] },
];
const clone = (x) => JSON.parse(JSON.stringify(x));
let current = clone(CASES[3]), P = null, steps = [], at = 0, timer = null, selected = null;
const VIEW = { w: 640, h: 360 };
const PSEUDO = ['SearchBundle(B):', '  Q ← 空的優先佇列；Reached ← 空', '  for each c with u(c) = source(B):', '    C ← SourceRange(c)', '    InsertLabels(c, C, SOURCE)', '  while Q 不是空的:', '    L₁ = (c₁, I₁, pred) ← 取出 key 最小的 Label', '    if v(c₁) = destination(B): return L₁', '    for each c₂ with u(c₂) = v(c₁):   // 不檢查節點是否走過', '      C ← StartRange(c₂, L₁)           // Head、Tail、扣預約', '      C ← BufferFilter(C, L₁, c₂)      // 只查最晚 s₁*', '      InsertLabels(c₂, C, L₁)          // 扣 Reached；一段一個 Label', '  return NO_PATH', '', 'Backtrack(L_goal):', '  最後一跳 s ← lo(I)', '  往前每跳 s ← I 中能接上的最大值'];
const lineOf = { init: 1, source: 3, insert: 4, pop: 6, goal: 7, range: 9, filter: 10, ins2: 11, dead: 8, finish: 15, nopath: 12 };

function build() {
  steps = []; P = parseInstance(current);
  const snap = (kind, ctx, x) => {
    const labels = ctx.labels.map((l) => ({ id: l.id, c: l.c, I: l.I, pred: l.pred, key: l.key, st: l.st }));
    steps.push({ kind, x, labels, Q: ctx.Q.map((l) => l.id), reached: Object.fromEntries(Object.entries(ctx.reached).map(([k, v]) => [k, v.map((p) => [...p])])) });
  };
  const res = solve(P, snap); at = 0; selected = null; return res;
}
const nm = (i) => `L${i + 1}`;
function explain(s) {
  const x = s.x, L = x.L1 && nm(x.L1.id);
  switch (s.kind) {
    case 'init': return ['初始化', `<p>Bundle ${P.S} MB 在 <b>${P.src}</b> 從第 ${P.g} 秒可傳送，要到 <b>${P.dst}</b>。Q 是空的。</p>`];
    case 'source': { const d = P.S.div(x.c.r); return [`來源：${x.c.id} 可起送範圍`, `<pre>Head = max(a, g) = max(${x.c.a}, ${P.g})\nTail = min(b − d, D* − d − δ) = min(${x.c.b} − ${d}, ${P.T} − ${d} − ${x.c.d})</pre><p>結果：${fmt(x.parts)}</p>`]; }
    case 'insert': { if (x.made.length) return [`建立 ${x.made.map((l) => nm(l.id)).join('、')}`, `<p>${x.made.map((l) => `<b>${nm(l.id)}</b> = (${l.c.id}, ${fmt([l.I])}, ${l.pred === null ? '來源' : nm(l.pred)})，key = ${l.key}`).join('<br>')}</p>${x.made.length > 1 ? '<p>同一條 contact 有不連通的區間，所以一段一個 Label。</p>' : ''}<p>Q 依 key 排序，同值先建立的先處理。</p>`]; return [`${x.c.id}：沒有新 Label`, `<p>${x.parts.length ? '這些時間都已到過，不用重算。' : '沒有可行的起送時間，所以這個方向不再延伸。'}</p>`]; }
    case 'pop': return [`取出 ${L}`, `<p><b>${L}</b> = (${x.L1.c.id}, ${fmt([x.L1.I])})，到節點 <b>${x.L1.c.v}</b>，key = ${x.L1.key}。</p><p>最早完整抵達時間最小，所以先處理。</p>`];
    case 'goal': return ['到達目的地', `<p><b>${L}</b> 已到 ${P.dst}。Q 依最早完整抵達排序，所以這是最早結果（候選結論，尚未正式證明）。</p>`];
    case 'dead': return ['沒有下一跳', `<p>節點 ${x.L1.c.v} 沒有 outgoing contact，這個 Label 到此結束。</p>`];
    case 'range': { const c1 = x.L1.c, c2 = x.c2, d1 = P.S.div(c1.r), d2 = P.S.div(c2.r), lo = x.L1.I[0]; const fast = d1.gt(d2) ? `<p>下一跳比較快，太早開始會沒資料可送，所以多等 d₁ − d₂ = ${d1.sub(d2)} 秒。</p>` : ''; return [`${L} → ${c2.id}：抓頭和尾`, `<pre>Head = max(a₂, lo + δ₁ + max(0, d₁ − d₂))\n     = max(${c2.a}, ${lo} + ${c1.d} + max(0, ${d1} − ${d2}))\nTail = min(b₂ − d₂, D* − d₂ − δ₂)\n     = min(${c2.b} − ${d2}, ${P.T} − ${d2} − ${c2.d})</pre>${c2.F.length ? `<p>預約 ${c2.F.map(([a, b]) => `[${a}, ${b})`).join('、')}：移除 ${c2.F.map(([a, b]) => `(${a.sub(d2)}, ${b})`).join('、')}。</p>` : ''}${fast}<p>候選：${fmt(x.parts)}</p>`]; }
    case 'filter': return [`${L} → ${x.c2.id}：檢查 ${x.c2.u} 的 buffer`, `<p>對每個 s₂，只查最晚的 s₁*：</p><pre>O(t) + 已收(t) − 已送(t) ≤ ${P.M}</pre><p>候選 ${fmt(x.parts)} → 結果 <b>${fmt(x.res)}</b></p>${x.parts.length && !x.res.length ? '<p class="badtxt">整段都放不下，這是「早到不一定比較好」的情況。</p>' : ''}<p>可在下方拖動 s₂ 查看。</p>`];
    case 'finish': {
      if (!x.goal) return [x.status === 'UNKNOWN' ? '未完成' : '找不到路徑', `<p>${x.status === 'UNKNOWN' ? '超過 Label 上限，結果未知。' : `Q 已空，期限 ${P.T} 內找不到路徑（在目前的限制範圍內）。`}</p>`];
      const prev = (i) => { const c = x.sch[i - 1]; return c.s.add(c.c.d).add(P.S.div(c.c.r)); };
      const rows = x.sch.map((h, i) => { const f = h.s.add(P.S.div(h.c.r)); const mode = i === 0 ? '來源' : (h.s.lt(prev(i)) ? '邊收邊轉' : '收完才轉'); return `${h.c.id}（${h.c.u}→${h.c.v}）：${h.s}～${f} 秒，${mode}`; }).join('<br>');
      return ['回溯完成', `<p>最早 <b>${x.goal.key} 秒</b>到 ${P.dst}。</p><p>${rows}</p><p>${x.valid ? '<span class="good">獨立重放通過</span>' : '<span class="badtxt">獨立重放失敗</span>'}${x.overlap ? '；<span class="badtxt">出現自我重疊，TRACK 尚未實作，這個答案未確認。</span>' : ''}</p>`];
    }
  }
  return ['', ''];
}
function pathOf(s, id) { const set = new Set(); let i = id; while (i !== null && i !== undefined) { set.add(s.labels[i].c.id); i = s.labels[i].pred; } return set; }
function edges(svg, nodes, marks = {}) {
  const pos = Object.fromEntries(nodes.map((n) => [n.id, n])); const pairs = {};
  const defs = sv('defs'); [['a', 'var(--win)'], ['cur', 'var(--cur)'], ['nxt', 'var(--nxt)'], ['path', 'var(--path)']].forEach(([k, c]) => { const m = sv('marker', { id: `m-${svg.id}-${k}`, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }); m.append(sv('path', { d: 'M0 0L10 5L0 10z', fill: c })); defs.append(m); }); svg.append(defs);
  current.contacts.forEach((c) => { const a = pos[c.u], b = pos[c.v]; if (!a || !b) return; const key = [c.u, c.v].sort().join('|'); const idx = (pairs[key] = (pairs[key] ?? -1) + 1);
    const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1, sign = c.u < c.v ? 1 : -1, bend = (idx + (key.includes('|') ? .35 : 0)) * 34 * sign * (idx % 2 ? -1 : 1) + 14 * sign;
    const mx = (a.x + b.x) / 2 - dy / len * bend, my = (a.y + b.y) / 2 + dx / len * bend, r = 21; const ux = mx - a.x, uy = my - a.y, ul = Math.hypot(ux, uy) || 1, vx = mx - b.x, vy = my - b.y, vl = Math.hypot(vx, vy) || 1;
    const off = current.contacts.some((o) => o.u === c.v && o.v === c.u) ? 34 : 16; const st = marks[c.id] || ''; const p = sv('path', { d: `M${a.x + ux / ul * r} ${a.y + uy / ul * r} Q${mx} ${my} ${b.x + vx / vl * r} ${b.y + vy / vl * r}`, class: `edge ${st}`, 'marker-end': `url(#m-${svg.id}-${st || 'a'})` }); svg.append(p);
    const nsx = -dy / len * Math.sign(bend || 1) * off, nsy = dx / len * Math.sign(bend || 1) * off; svg.append(sv('text', { x: (a.x + 2 * mx + b.x) / 4 + nsx, y: (a.y + 2 * my + b.y) / 4 + nsy, class: 'halo', 'text-anchor': 'middle', 'dominant-baseline': 'central' }, `${c.id} [${c.a},${c.b}]`)); });
}
function drawGraph() {
  const svg = $('#graph'); svg.replaceChildren(); svg.setAttribute('viewBox', `0 0 ${VIEW.w} ${VIEW.h}`);
  const s = steps[at], x = s.x, marks = {}; const shown = selected !== null && s.labels[selected] ? selected : (s.kind === 'finish' && x.goal ? x.goal.id : null);
  if (shown !== null) pathOf(s, shown).forEach((id) => { marks[id] = 'path'; });
  if (x.L1 && s.kind !== 'goal') marks[x.L1.c.id] = marks[x.L1.c.id] || 'cur'; if (x.c2) marks[x.c2.id] = 'nxt'; if (s.kind === 'source') marks[x.c.id] = 'nxt';
  edges(svg, current.nodes, marks);
  const curN = x.L1 ? x.L1.c.v : (s.kind === 'init' ? P.src : null);
  current.nodes.forEach((n) => { const cl = ['node', n.id === P.src ? 'src' : '', n.id === P.dst ? 'dst' : '', n.id === curN ? 'cur' : ''].join(' '); svg.append(sv('circle', { cx: n.x, cy: n.y, r: 20, class: cl })); svg.append(sv('text', { x: n.x, y: n.y, class: 'nodet' }, n.id)); });
}
function drawLabels() {
  const s = steps[at], x = s.x, t = $('#labels'); t.replaceChildren(); const newIds = new Set((x.made || []).map((l) => l.id));
  t.append(el('tr', {}, el('th', { text: 'Label' }), el('th', { text: 'Contact' }), el('th', { text: '區間 I' }), el('th', { text: 'key' }), el('th', { text: '前驅' }), el('th', { text: '狀態' })));
  const cur = x.L1 ? x.L1.id : null; const gid = x.goal ? x.goal.id : null;
  s.labels.forEach((l) => { const state = l.id === gid ? '目的地' : l.id === cur ? '處理中' : s.Q.includes(l.id) ? `Q 第 ${s.Q.indexOf(l.id) + 1}` : '已處理'; const b = el('button', { text: nm(l.id), title: '顯示前驅路徑' }); b.onclick = () => { selected = selected === l.id ? null : l.id; drawGraph(); };
    t.append(el('tr', { class: l.id === gid ? 'goal' : l.id === cur ? 'current' : newIds.has(l.id) ? 'new' : '' }, el('td', {}, b), el('td', { text: l.c.id }), el('td', { text: fmt([l.I]) }), el('td', { text: String(l.key) }), el('td', { text: l.pred === null ? '來源' : nm(l.pred) }), el('td', { class: 'pill', text: state }))); });
  if (!s.labels.length) t.append(el('tr', {}, el('td', { colspan: 6, text: '還沒有 Label', class: 'pill' })));
  $('#qtext').textContent = `Q：${s.Q.length ? s.Q.map(nm).join('、') : '空'}`;
}
function drawTimeline() {
  const s = steps[at], x = s.x, box = $('#timeline'); box.replaceChildren(); const tl = el('div', { class: 'tl' }); const tmax = Math.max(P.T.num() > 0 ? 0 : 1, ...P.cs.map((c) => c.b.num())) || 1; const pct = (v) => `${Math.max(0, Math.min(100, v / tmax * 100))}%`; const seg = (cl, a, b) => { const i = el('i', { class: cl }); i.style.left = pct(a); i.style.width = pct(b - a); return i; };
  const focus = x.c2 ? x.c2.id : (x.c ? x.c.id : null);
  P.cs.forEach((c) => { const bar = el('div', { class: 'bar' }); bar.append(seg('win', c.a.num(), c.b.num())); c.F.forEach(([a, b]) => bar.append(seg('res', a.num(), b.num()))); (s.reached[c.id] || []).forEach(([a, b]) => bar.append(seg('rea', a.num(), b.num()))); if (focus === c.id) { const list = s.kind === 'filter' ? x.res : s.kind === 'insert' ? x.nw : x.parts; (list || []).forEach(([a, b]) => bar.append(seg('can', a.num(), b.num()))); } tl.append(el('div', { class: focus === c.id ? 'on' : '', text: c.id }), bar); });
  const axis = el('div', { class: 'axis' }); const step = tmax > 40 ? 10 : tmax > 15 ? 5 : tmax > 6 ? 2 : 1; for (let t = 0; t <= tmax; t += step) { const sp = el('span', { text: String(t) }); sp.style.left = pct(t); axis.append(sp); } tl.append(axis); box.append(tl);
}
function bufferInfo() { const s = steps[at], x = s.x; if ((s.kind === 'filter' || s.kind === 'range' || s.kind === 'insert') && x.L1 && (x.c2 || x.c)) return { c1: x.L1.c, c2: x.c2 || x.c, I: [x.L1.I], parts: s.kind === 'insert' ? [] : x.parts }; return null; }
function drawBuffer() {
  const s = steps[at], x = s.x, svg = $('#buffer'), info = bufferInfo(), row = $('#s2-row'), W = Math.max(svg.clientWidth || 900, 300), H = 230, M = { l: 40, r: 14, t: 26, b: 28 }; svg.replaceChildren(); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  let n, cv, chosen = null;
  if (info && info.parts.length) { n = info.c1.v; const lo = info.parts[0][0], hi = info.parts[info.parts.length - 1][1]; row.hidden = false; const f = +$('#s2').value / 200; const raw = new R(BigInt(Math.round(f * 200))).div(200).mul(hi.sub(lo)).add(lo); chosen = raw; const inPart = info.parts.some(([a, b]) => a.le(raw) && raw.le(b)); const r = feasibleAt(P, info.I, info.c1, info.c2, raw); const ok = inPart && r.ok; $('#s2-val').textContent = `s₂ = ${raw.num().toFixed(2)}${r.s1 ? `，s₁* = ${r.s1.num().toFixed(2)}` : ''}`; $('#buf-state').innerHTML = !inPart ? '<span class="badtxt">不在候選內（已預約）</span>' : ok ? '<span class="good">放得下</span>' : '<span class="badtxt">放不下</span>'; cv = { r, ok }; }
  else { row.hidden = true; const sch = x.sch; if (s.kind === 'finish' && sch) { n = sch.length > 1 ? sch[1].c.u : sch[0].c.v; } else n = x.L1 ? x.L1.c.v : P.src; $('#buf-state').textContent = '選到下一跳時，可拖動 s₂'; }
  $('#buf-title').textContent = `節點 ${n} 的 Buffer`; const O = P.O[n] || []; const tmax = Math.max(...P.cs.map((c) => c.b.num()), 1), ymax = Math.max(P.M.add(P.S).num() * 1.1, 1); const X = (t) => M.l + t / tmax * (W - M.l - M.r), Y = (v) => H - M.b - v / ymax * (H - M.t - M.b);
  const step = (W < 500 ? 2 : 1) * (tmax > 40 ? 10 : tmax > 15 ? 5 : tmax > 6 ? 2 : 1); for (let t = 0; t <= tmax; t += step) { svg.append(sv('text', { x: X(t), y: H - 10, class: 'muted', 'text-anchor': 'middle' }, t)); svg.append(sv('line', { x1: X(t), y1: M.t, x2: X(t), y2: H - M.b, stroke: 'var(--line)', 'stroke-width': .5 })); }
  svg.append(sv('line', { x1: M.l, y1: Y(0), x2: W - M.r, y2: Y(0), stroke: 'var(--muted)' })); svg.append(sv('line', { x1: M.l, y1: Y(P.M.num()), x2: W - M.r, y2: Y(P.M.num()), stroke: 'var(--bad)', 'stroke-dasharray': '6 4' })); svg.append(sv('text', { x: M.l - 6, y: Y(P.M.num()), 'text-anchor': 'end', 'dominant-baseline': 'central', class: 'muted' }, `${P.M}`)); svg.append(sv('text', { x: M.l - 6, y: Y(0), 'text-anchor': 'end', 'dominant-baseline': 'central', class: 'muted' }, '0'));
  const curve = [new R(0n), ...O.map((p) => p[0]), R.of(tmax)]; const pts = curve.map((t) => `${X(t.num())},${Y(occ(O, t).num())}`).join(' '); svg.append(sv('polyline', { points: pts, fill: 'none', stroke: 'var(--muted)', 'stroke-width': 2 }));
  if (cv && cv.r.s1) { const { h, A, f } = cv.r; const ts = [new R(0n), h, A, chosen, f, ...O.map((p) => p[0]), R.of(tmax)].sort((a, b) => a.cmp(b)); const start = h; const tot = ts.filter((t) => t.ge(start) && t.le(f)).map((t) => `${X(t.num())},${Y(occ(O, t).add(ramp(t, h, A, P.S)).sub(ramp(t, chosen, f, P.S)).num())}`).join(' '); svg.append(sv('polyline', { points: tot, fill: 'none', stroke: cv.ok ? 'var(--can)' : 'var(--bad)', 'stroke-width': 3 })); svg.append(sv('text', { x: M.l, y: 14 }, '粗線：背景＋本包')); }
  svg.append(sv('text', { x: W - M.r, y: 14, 'text-anchor': 'end', class: 'muted' }, W < 500 ? '灰：背景　紅虛線：上限' : '灰線：背景　紅虛線：上限'));
}
function draw() {
  const s = steps[at]; $('#seek').max = steps.length - 1; $('#seek').value = at; $('#stepno').textContent = `${at + 1} / ${steps.length}`;
  const [t, b] = explain(s); $('#exp-title').textContent = t; $('#exp-body').innerHTML = b;
  const ln = s.kind === 'insert' && s.x.pred !== null ? lineOf.ins2 : s.kind === 'finish' && !s.x.goal ? lineOf.nopath : lineOf[s.kind]; const code = $('#sub-code'); code.replaceChildren(...PSEUDO.map((l, i) => el('span', { class: i === ln ? 'on' : '', text: l || ' ' })));
  const log = $('#sub-log'); log.replaceChildren(...steps.slice(0, at + 1).map((x, i) => el('li', { class: i === at ? 'on' : '', text: explain(x)[0] }))); log.scrollTop = log.scrollHeight;
  drawGraph(); drawLabels(); drawTimeline(); drawBuffer();
}
function stopPlay() { if (timer) clearInterval(timer); timer = null; $('#play').textContent = '播放'; }
function go(i) { at = Math.max(0, Math.min(steps.length - 1, i)); const info = bufferInfo(); if (info && info.parts.length) { $('#s2').value = 0; } draw(); }
function run() { stopPlay(); build(); go(0); }
function parseBg(t) { t = t.trim(); if (!t) return []; return t.split(',').map((x) => { const m = x.trim().split(':'); if (m.length !== 2) throw new Error(`背景格式不正確：${x}`); return [m[0].trim(), m[1].trim()]; }); }
function parseF(t) { t = t.trim(); if (!t) return []; return t.split(',').map((x) => { const m = x.trim().split('-'); if (m.length !== 2) throw new Error(`預約格式不正確：${x}`); return [m[0].trim(), m[1].trim()]; }); }
function fillEdit() {
  const f = $('#bundle-fields'); f.replaceChildren(); const nodes = current.nodes.map((n) => n.id);
  const inp = (k, lab) => { const i = el('input', { type: 'text', value: String(current[k]) }); i.oninput = () => { current[k] = i.value; }; f.append(el('label', {}, lab, i)); };
  const sel = (k, lab) => { const s = el('select'); nodes.forEach((n) => s.append(el('option', { value: n, text: n }))); s.value = current[k]; s.onchange = () => { current[k] = s.value; }; f.append(el('label', {}, lab, s)); };
  sel('src', '來源'); sel('dst', '目的地'); inp('g', '可傳送時間 g'); inp('S', '大小 S'); inp('M', '上限 M'); inp('T', '期限 D*');
  const nt = $('#node-table'); nt.replaceChildren(el('tr', {}, el('th', { text: '節點' }), el('th', { text: '背景占用' }), el('th')));
  current.nodes.forEach((n, i) => { const id = el('input', { type: 'text', value: n.id, 'aria-label': '節點名稱' }); id.onchange = () => { const old = n.id; n.id = id.value.trim(); current.contacts.forEach((c) => { if (c.u === old) c.u = n.id; if (c.v === old) c.v = n.id; }); if (current.src === old) current.src = n.id; if (current.dst === old) current.dst = n.id; fillEdit(); }; const bg = el('input', { type: 'text', class: 'w2', value: (n.bg || []).map(([a, b]) => `${a}:${b}`).join(', '), 'aria-label': '背景占用' }); bg.onchange = () => { try { n.bg = parseBg(bg.value); $('#edit-msg').textContent = ''; } catch (e) { $('#edit-msg').textContent = e.message; } }; const del = el('button', { class: 'del', text: '刪除' }); del.onclick = () => { current.nodes.splice(i, 1); current.contacts = current.contacts.filter((c) => c.u !== n.id && c.v !== n.id); fillEdit(); }; nt.append(el('tr', {}, el('td', {}, id), el('td', {}, bg), el('td', {}, del))); });
  const ct = $('#contact-table'); ct.replaceChildren(el('tr', {}, ...['編號', '傳送端', '接收端', '開始', '結束', '速率', '延遲', '已預約', ''].map((h) => el('th', { text: h }))));
  current.contacts.forEach((c, i) => { const tx = (k) => { const e = el('input', { type: 'text', value: String(c[k]), 'aria-label': k }); e.oninput = () => { c[k] = e.value; }; return e; }; const nd = (k) => { const s = el('select', { 'aria-label': k }); nodes.forEach((n) => s.append(el('option', { value: n, text: n }))); s.value = c[k]; s.onchange = () => { c[k] = s.value; drawEdit(); }; return s; }; const fx = el('input', { type: 'text', class: 'w2', value: (c.F || []).map(([a, b]) => `${a}-${b}`).join(', '), 'aria-label': '已預約' }); fx.onchange = () => { try { c.F = parseF(fx.value); $('#edit-msg').textContent = ''; } catch (e) { $('#edit-msg').textContent = e.message; } }; const del = el('button', { class: 'del', text: '刪除' }); del.onclick = () => { current.contacts.splice(i, 1); fillEdit(); }; ct.append(el('tr', {}, el('td', {}, tx('id')), el('td', {}, nd('u')), el('td', {}, nd('v')), el('td', {}, tx('a')), el('td', {}, tx('b')), el('td', {}, tx('r')), el('td', {}, tx('d')), el('td', {}, fx), el('td', {}, del))); });
  drawEdit();
}
function drawEdit() { const svg = $('#edit-graph'); svg.replaceChildren(); svg.setAttribute('viewBox', `0 0 ${VIEW.w} ${VIEW.h}`); edges(svg, current.nodes); current.nodes.forEach((n) => { const g = sv('g', { class: 'nd' }); g.append(sv('circle', { cx: n.x, cy: n.y, r: 20, class: `node ${n.id === current.src ? 'src' : ''} ${n.id === current.dst ? 'dst' : ''}` })); g.append(sv('text', { x: n.x, y: n.y, class: 'nodet' }, n.id)); g.addEventListener('pointerdown', (e) => { e.preventDefault(); const move = (ev) => { const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; const q = pt.matrixTransform(svg.getScreenCTM().inverse()); n.x = Math.max(24, Math.min(VIEW.w - 24, q.x)); n.y = Math.max(24, Math.min(VIEW.h - 24, q.y)); drawEdit(); }; const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); }; window.addEventListener('pointermove', move); window.addEventListener('pointerup', up); }); svg.append(g); }); }
function tab(name) { document.querySelectorAll('.tabs button').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name))); document.querySelectorAll('.tab').forEach((t) => { t.hidden = t.id !== `tab-${name}`; }); if (name === 'edit') fillEdit(); }
document.querySelectorAll('.tabs button').forEach((b) => { b.onclick = () => tab(b.dataset.tab); });
document.querySelectorAll('.subtabs button').forEach((b) => { b.onclick = () => { document.querySelectorAll('.subtabs button').forEach((x) => x.setAttribute('aria-selected', String(x === b))); $('#sub-exp').hidden = b.dataset.sub !== 'exp'; $('#sub-code').hidden = b.dataset.sub !== 'code'; $('#sub-log').hidden = b.dataset.sub !== 'log'; }; });
['#case', '#edit-case'].forEach((q) => { const s = $(q); CASES.forEach((c, i) => s.append(el('option', { value: i, text: c.name }))); s.value = 3; });
$('#case').onchange = () => { current = clone(CASES[+$('#case').value]); $('#edit-case').value = $('#case').value; run(); };
$('#load-case').onclick = () => { current = clone(CASES[+$('#edit-case').value]); $('#case').value = $('#edit-case').value; fillEdit(); run(); };
$('#first').onclick = () => { stopPlay(); go(0); }; $('#last').onclick = () => { stopPlay(); go(steps.length - 1); }; $('#prev').onclick = () => { stopPlay(); go(at - 1); }; $('#next').onclick = () => { stopPlay(); go(at + 1); }; $('#seek').oninput = () => { stopPlay(); go(+$('#seek').value); }; $('#s2').oninput = () => drawBuffer();
$('#play').onclick = () => { if (timer) return stopPlay(); $('#play').textContent = '暫停'; timer = setInterval(() => { if (at >= steps.length - 1) return stopPlay(); go(at + 1); }, 1100); };
document.addEventListener('keydown', (e) => { if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) return; if (e.key === 'ArrowRight') { stopPlay(); go(at + 1); } if (e.key === 'ArrowLeft') { stopPlay(); go(at - 1); } });
$('#add-node').onclick = () => { let i = 1; while (current.nodes.some((n) => n.id === `N${i}`)) i++; current.nodes.push({ id: `N${i}`, x: 320, y: 180 }); fillEdit(); };
$('#add-contact').onclick = () => { let i = 1; while (current.contacts.some((c) => c.id === `c${i}`)) i++; current.contacts.push(c0(`c${i}`, current.nodes[0]?.id, current.nodes[1]?.id, 0, 10, 2)); fillEdit(); };
$('#apply').onclick = () => { try { build(); go(0); $('#edit-msg').textContent = ''; tab('run'); } catch (e) { $('#edit-msg').textContent = e.message; } };
$('#export').onclick = () => { const a = el('a', { href: URL.createObjectURL(new Blob([JSON.stringify(current, null, 2)], { type: 'application/json' })), download: 'topology.json' }); a.click(); URL.revokeObjectURL(a.href); };
$('#import').onchange = async (e) => { try { const j = JSON.parse(await e.target.files[0].text()); parseInstance(j); current = { ...j, nodes: j.nodes.map((n, i) => ({ x: 90 + (i * 110) % 480, y: 90 + (i * 83) % 200, ...n })) }; fillEdit(); $('#edit-msg').textContent = ''; } catch (x) { $('#edit-msg').textContent = `無法讀取：${x.message}`; } };
try { run(); } catch (e) { $('#exp-title').textContent = '無法執行'; $('#exp-body').textContent = e.message; }
