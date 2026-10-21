"""按需區間處理的隔離驗證；不是路由搜尋或論文 Algorithm 2 重現。

固定模型：連續分段線性背景、逐 byte 送收、非搶占傳輸、固定速率。
Fraction 精確計算時間／資料量；不包含跳變、前驅等待、Label 或 dominance。
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
from fractions import Fraction as Q
import gc
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import time
import tracemalloc


Curve = tuple[tuple[Q, Q], ...]
Intervals = tuple[tuple[Q, Q], ...]


@dataclass(frozen=True)
class Contact:
    cid: int
    u: int
    v: int
    start: Q
    end: Q
    rate: Q
    delay: Q
    quota: Q
    busy: Intervals = ()


@dataclass
class Snapshot:
    contacts: tuple[Contact, ...]
    curves: tuple[Curve, ...]
    limits: tuple[Q, ...]
    node_versions: tuple[int, ...]
    contact_versions: tuple[int, ...]


def value(curve: Curve, t: Q) -> Q:
    """僅供區間求解器；定義域外延用端值。"""
    if t <= curve[0][0]:
        return curve[0][1]
    for (a, x), (b, y) in zip(curve, curve[1:]):
        if t <= b:
            return x + (y - x) * (t - a) / (b - a)
    return curve[-1][1]


def fixed_start_check(c: Contact, state: Snapshot, size: Q, deadline: Q,
                      s: Q) -> bool:
    """獨立固定排程檢查：在各 ramp 端點與背景折點檢查全時段峰值。

    不使用區間分割／裁切程序。兩個線性函式之和在各小段為線性，
    故固定 s 時檢查這些點涵蓋整段時間，不是逐秒 sampling。
    """
    d = size / c.rate
    if size > c.quota or s < c.start or s + d > c.end:
        return False
    if s + d + c.delay > deadline:
        return False
    if any(s < b and a < s + d for a, b in c.busy):
        return False
    for node, begin, end, receiving in (
        (c.u, s, s + d, False),
        (c.v, s + c.delay, s + c.delay + d, True),
    ):
        points = state.curves[node]
        times = {begin, end} | {t for t, _ in points if begin <= t <= end}
        for t in times:
            # 用獨立插值寫法，降低與 solver 共用錯誤的風險。
            if t <= points[0][0]:
                background = points[0][1]
            elif t >= points[-1][0]:
                background = points[-1][1]
            else:
                a, x, b, y = next((a, x, b, y) for (a, x), (b, y)
                                  in zip(points, points[1:]) if a <= t <= b)
                background = (x * (b - t) + y * (t - a)) / (b - a)
            added = c.rate * (t - begin) if receiving else size - c.rate * (t - begin)
            if background + added > state.limits[node]:
                return False
    return True


def merge(parts: list[tuple[Q, Q]]) -> Intervals:
    result: list[tuple[Q, Q]] = []
    for lo, hi in sorted(parts):
        if result and lo <= result[-1][1]:
            result[-1] = (result[-1][0], max(hi, result[-1][1]))
        else:
            result.append((lo, hi))
    return tuple(result)


def feasible_starts(c: Contact, state: Snapshot, size: Q, deadline: Q) -> Intervals:
    """求固定 contact 的精確可行起送集合 J；尚未加入前驅等待限制。

    將起送 s 以背景折點對齊 ramp 端點的事件切開。每格內每個峰值
    約束均為 s 的仿射函式，直接求線性不等式交集；沒有時間格點。
    """
    if size > c.quota:
        return ()
    d = size / c.rate
    lo, hi = c.start, min(c.end - d, deadline - d - c.delay)
    if lo > hi:
        return ()
    cuts = {lo, hi}
    for node, shift in ((c.u, Q(0)), (c.v, c.delay)):
        for t, _ in state.curves[node]:
            cuts.update(x for x in (t - shift, t - shift - d) if lo < x < hi)
    for a, b in c.busy:
        cuts.update(x for x in (a - d, b) if lo < x < hi)
    cuts = sorted(cuts)
    parts = []
    for left, right in zip(cuts, cuts[1:]):
        middle = (left + right) / 2
        if any(middle < b and a < middle + d for a, b in c.busy):
            continue
        lower, upper = left, right
        for node, shift, receiving in ((c.u, Q(0), False), (c.v, c.delay, True)):
            begin, finish = middle + shift, middle + shift + d
            # 峰值只可能出現在 ramp 端點或其內部背景折點。
            probes = [('moving', shift), ('moving', shift + d)]
            probes += [('fixed', t) for t, _ in state.curves[node]
                       if begin < t < finish]
            for kind, param in probes:
                def margin(s):
                    t = s + param if kind == 'moving' else param
                    elapsed = t - s - shift
                    extra = c.rate * elapsed if receiving else size - c.rate * elapsed
                    return state.limits[node] - value(state.curves[node], t) - extra
                ml, mr = margin(left), margin(right)
                slope = (mr - ml) / (right - left)
                if slope > 0:
                    lower = max(lower, left - ml / slope)
                elif slope < 0:
                    upper = min(upper, left - ml / slope)
                elif ml < 0:
                    lower, upper = Q(1), Q(0)
                    break
            if lower > upper:
                break
        if lower <= upper:
            parts.append((lower, upper))
    # Contact 恰好容一包、以及兩個禁止區間之間的單點，不能漏掉。
    for point in cuts:
        if fixed_start_check(c, state, size, deadline, point):
            parts.append((point, point))
    return merge(parts)


STRATEGIES = ('eager_rebuild', 'lazy_roundcache', 'eager_incremental', 'lazy_incremental')


class Engine:
    """四種策略共用同一 solver；差別只在何時求解與保留結果。"""
    def __init__(self, strategy):
        self.strategy = strategy
        self.cache = {}
        self.solves = self.hits = self.fragments = 0
        self.peak_entries = 0

    def query(self, state, cid, size, deadline):
        c = state.contacts[cid]
        stamp = (state.contact_versions[cid], state.node_versions[c.u],
                 state.node_versions[c.v], size, deadline)
        # 每條 contact 僅保留最近一個 context，避免版本永久累積。
        old = self.cache.get(cid)
        if old is not None and old[0] == stamp:
            self.hits += 1
            return old[1]
        result = feasible_starts(c, state, size, deadline)
        self.cache[cid] = (stamp, result)
        self.solves += 1
        self.fragments += len(result)
        self.peak_entries = max(self.peak_entries, len(self.cache))
        return result

    def begin(self, state, size, deadline):
        if self.strategy in ('eager_rebuild', 'lazy_roundcache'):
            self.cache.clear()
        if self.strategy.startswith('eager'):
            for cid in range(len(state.contacts)):
                self.query(state, cid, size, deadline)


def plain_state(c, sender=((0, 0), (20, 0)), receiver=((0, 0), (20, 0)), limit=4):
    curves = tuple(tuple((Q(t), Q(v)) for t, v in pts) for pts in (sender, receiver))
    return Snapshot((c,), curves, (Q(limit), Q(limit)), (0, 0), (0,))


def correctness(seed=1021):
    c = Contact(0, 0, 1, Q(1), Q(10), Q(4), Q(0), Q(40))
    release = ((0, 4), (7, 4), (8, 0), (20, 0))
    cases = [
        ('empty', c, plain_state(c), Q(4), ((Q(1), Q(9)),)),
        ('simultaneous_release_receive', c, plain_state(c, receiver=release), Q(4), ((Q(7), Q(9)),)),
        ('sender_ramp', c, plain_state(c, sender=((0, 0), (2, 0), (3, 4), (6, 4), (7, 0), (20, 0))), Q(4), ((Q(1), Q(2)), (Q(7), Q(9)))),
        ('busy_slots', replace(c, busy=((Q(3), Q(5)),)), plain_state(c), Q(4), ((Q(1), Q(2)), (Q(5), Q(9)))),
        ('delay_shift', replace(c, delay=Q(1)), plain_state(c, receiver=release), Q(4), ((Q(6), Q(9)),)),
        ('quota_reject', replace(c, quota=Q(3)), plain_state(c), Q(4), ()),
        ('deadline', c, plain_state(c), Q(4), ((Q(1), Q(5)),)),
        ('one_point', replace(c, end=Q(2)), plain_state(c), Q(4), ((Q(1), Q(1)),)),
        ('rational_boundary', replace(c, start=Q(0), end=Q(5)),
         plain_state(c, receiver=((0, 4), (Q(7, 3), 4), (Q(10, 3), 0), (20, 0))),
         Q(4), ((Q(7, 3), Q(4)),)),
    ]
    results = []
    for name, contact, state, size, expected in cases:
        deadline = Q(6) if name == 'deadline' else Q(20)
        actual = feasible_starts(contact, state, size, deadline)
        if actual != expected:
            raise AssertionError((name, actual, expected))
        results.append(dict(case=name, expected=string_intervals(expected), actual=string_intervals(actual), passed=True))
    rng = random.Random(seed)
    checks = 0
    for trial in range(100):
        pts = lambda: tuple((Q(t), Q(rng.randrange(0, 9))) for t in (0, 3, 6, 10, 15, 20))
        rate, size = Q(rng.choice((2, 3, 4))), Q(rng.choice((1, 2, 4)))
        contact = replace(c, rate=rate, delay=Q(rng.choice((0, 1, 2))),
                          busy=((Q(4), Q(5)), (Q(8), Q(9))))
        state = Snapshot((contact,), (pts(), pts()), (Q(8), Q(8)), (0, 0), (0,))
        intervals = feasible_starts(contact, state, size, Q(20))
        probes = {Q(i, 7) for i in range(0, 85)}
        for a, b in intervals:
            probes.update((a, b, (a + b) / 2, a - Q(1, 1000), b + Q(1, 1000)))
        for s in probes:
            predicted = any(a <= s <= b for a, b in intervals)
            actual = fixed_start_check(contact, state, size, Q(20), s)
            checks += 1
            if predicted != actual:
                raise AssertionError(dict(trial=trial, start=str(s), predicted=predicted, actual=actual))
    return dict(analytic=results, random_fixed_start_checks=checks, seed=seed,
                scope='Exact rational continuous curves; finite probes do not prove interval completeness')


def string_intervals(xs):
    return [[str(a), str(b)] for a, b in xs]


def make_curve(rng, fragmented=False):
    times = (0, 4, 8, 12, 16, 20, 24, 28, 32) if fragmented else (0, 8, 16, 24, 32)
    return tuple((Q(t), Q(rng.choice((0, 0, 2, 4, 6, 8)))) for t in times)


def make_workload(seed, count, epochs, fraction, update, varying=False, fragmented=False):
    """合成資源快照＋查詢序列；不是由完整前包路由提交產生的 traffic trace。"""
    rng = random.Random(seed)
    nodes = max(8, count // 4)
    contacts = []
    for cid in range(count):
        u = rng.randrange(nodes)
        v = (u + rng.randrange(1, nodes)) % nodes
        start = Q(rng.randrange(0, 10))
        busy = ((Q(12), Q(13)),) if cid % 3 == 0 else ()
        contacts.append(Contact(cid, u, v, start, start + 18, Q(rng.choice((2, 4))),
                                Q(rng.choice((0, 1))), Q(80), busy))
    curves = tuple(make_curve(rng, fragmented) for _ in range(nodes))
    nv, cv = [0] * nodes, [0] * count
    state = Snapshot(tuple(contacts), curves, (Q(8),) * nodes, tuple(nv), tuple(cv))
    # 固定探索區域便於觀察跨快照 reuse；探索比例是受控變因，不是假稱真實搜尋結果。
    selected = rng.sample(range(count), max(1, math.ceil(count * fraction)))
    stream = []
    for epoch in range(epochs):
        if epoch:
            changed_nodes = rng.sample(range(nodes), max(1, math.ceil(nodes * update)))
            changed_contacts = rng.sample(range(count), max(1, math.ceil(count * update)))
            curves2 = list(state.curves)
            contacts2 = list(state.contacts)
            for node in changed_nodes:
                curves2[node] = make_curve(rng, fragmented)
                nv[node] += 1
            for cid in changed_contacts:
                # 全快照替換 slot，避免不合法的重疊 reservations。
                slot = Q(10 + epoch % 5)
                contacts2[cid] = replace(contacts2[cid], busy=((slot, slot + 1),))
                cv[cid] += 1
            state = Snapshot(tuple(contacts2), tuple(curves2), state.limits, tuple(nv), tuple(cv))
        ids = selected.copy()
        rng.shuffle(ids)
        ids += ids[:max(1, len(ids) // 3)]  # 同一 contact 被多個候選探索的查詢重複。
        stream.append((state, Q((2, 4, 6)[epoch % 3] if varying else 4), Q(32), tuple(ids)))
    return stream


def run_engine(strategy, stream, collect=False):
    engine = Engine(strategy)
    answers = []
    for state, size, deadline, queries in stream:
        engine.begin(state, size, deadline)
        for cid in queries:
            answer = engine.query(state, cid, size, deadline)
            if collect:
                answers.append(answer)
    return engine, answers


def stat(values):
    xs = sorted(values)
    return dict(mean=statistics.mean(xs), minimum=min(xs), maximum=max(xs),
                stddev=statistics.stdev(xs) if len(xs) > 1 else 0,
                median=statistics.median(xs), p95=xs[math.ceil(.95 * len(xs)) - 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('output/demand_interval_validation_20261021'))
    parser.add_argument('--contacts', type=int, default=96)
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    if min(args.contacts, args.epochs, args.repeats) < 1:
        parser.error('all counts must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    try:
        checks = correctness()
        specs = [
            ('sparse_local', .1, .02, False, False),
            ('half_local', .5, .02, False, False),
            ('full_local', 1., .02, False, False),
            ('sparse_global', .1, 1., False, False),
            ('full_global', 1., 1., False, False),
            ('varying_sizes', .1, .02, True, False),
            ('fragmented', .1, .02, False, True),
        ]
        streams = {}
        equality_queries = 0
        for name, fraction, update, varying, fragmented in specs:
            # 3 seeds for correctness; only seed 1021 for repeated timing below.
            for seed in (1021, 1022, 1023):
                stream = make_workload(seed, args.contacts, args.epochs, fraction, update, varying, fragmented)
                reference = [feasible_starts(state.contacts[cid], state, size, deadline)
                             for state, size, deadline, ids in stream for cid in ids]
                for strategy in STRATEGIES:
                    _, answers = run_engine(strategy, stream, collect=True)
                    if answers != reference:
                        raise AssertionError(dict(case=name, seed=seed, strategy=strategy, error='cache mismatch'))
                    equality_queries += len(reference)
                if seed == 1021:
                    streams[name] = stream
            print(f'correctness {name}: passed', flush=True)
        checks['cache_answer_comparisons'] = equality_queries
        # 任一 correctness failure 會在這裡之前中止，禁止繼續效能比較。
        (args.output / 'correctness.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
        raw = []
        order_rng = random.Random(21021)
        for name, stream in streams.items():
            # 暖機所有策略；快取 instance 不跨 run 保留。
            for strategy in STRATEGIES:
                run_engine(strategy, stream)
            for repeat in range(args.repeats):
                order = list(STRATEGIES)
                order_rng.shuffle(order)
                for strategy in order:
                    gc.collect()
                    start = time.perf_counter_ns()
                    engine, _ = run_engine(strategy, stream)
                    elapsed = (time.perf_counter_ns() - start) / 1e6
                    raw.append(dict(scenario=name, strategy=strategy, repeat=repeat,
                                    elapsed_ms=elapsed, solves=engine.solves, hits=engine.hits,
                                    fragments_generated=engine.fragments, peak_entries=engine.peak_entries))
            print(f'timing {name}: done', flush=True)
        summary = []
        for name, stream in streams.items():
            for strategy in STRATEGIES:
                rows = [r for r in raw if r['scenario'] == name and r['strategy'] == strategy]
                # 記憶體另跑一次，避免 tracemalloc 污染時間；不含事先建立的輸入。
                gc.collect()
                tracemalloc.start()
                engine, _ = run_engine(strategy, stream)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                xs = stat([r['elapsed_ms'] for r in rows])
                summary.append(dict(scenario=name, strategy=strategy, **{f'ms_{k}': v for k, v in xs.items()},
                                    peak_python_bytes=peak, solves=engine.solves, hits=engine.hits,
                                    fragments_generated=engine.fragments, peak_entries=engine.peak_entries))
        for filename, rows in (('timings.csv', raw), ('summary.csv', summary)):
            with (args.output / filename).open('w', newline='', encoding='utf-8-sig') as out:
                writer = csv.DictWriter(out, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        inputs = []
        for name, stream in streams.items():
            for epoch, (state, size, deadline, ids) in enumerate(stream):
                inputs.append(dict(scenario=name, epoch=epoch, size=str(size), deadline=str(deadline), queries=list(ids),
                    contacts=[dict(cid=c.cid, u=c.u, v=c.v, start=str(c.start), end=str(c.end), rate=str(c.rate),
                                   delay=str(c.delay), quota=str(c.quota), busy=string_intervals(c.busy)) for c in state.contacts],
                    curves=[[[str(t), str(v)] for t, v in curve] for curve in state.curves],
                    limits=[str(v) for v in state.limits], node_versions=state.node_versions, contact_versions=state.contact_versions))
        encoded = json.dumps(inputs, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        (args.output / 'inputs.json').write_bytes(encoded)
        meta = dict(python=sys.version, platform=platform.platform(), processor=platform.processor(),
                    contacts=args.contacts, epochs=args.epochs, repeats=args.repeats,
                    timing_seed=1021, correctness_seeds=[1021, 1022, 1023],
                    input_sha256=hashlib.sha256(encoded).hexdigest(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    total_seconds=time.perf_counter() - started,
                    scope='Component benchmark, continuous background only; no path search, waiting, commits, jumps, or paper reproduction')
        (args.output / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
        print(json.dumps(dict(output=str(args.output), checks=checks['random_fixed_start_checks'],
                              cache_comparisons=equality_queries, seconds=meta['total_seconds']), ensure_ascii=False), flush=True)
    except Exception as exc:
        (args.output / 'FAILURE.json').write_text(json.dumps(dict(error=repr(exc), performance_stopped=True), indent=2), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
