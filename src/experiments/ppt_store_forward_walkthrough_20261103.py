"""Reproduce the 1013 PPT topology with the 2026-11-03 candidate.

This is a small presentation walkthrough, not a research-scale experiment.
The candidate and its production definitions are not modified.  The independent
checker includes source and destination occupancy, which the candidate's Commit
does not yet record.  This fixture has distinct sources and disjoint destination
receptions, so that omission does not change its two selected routes.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import heapq
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "store_forward"))
import store_label as SL
from cut_through_audit import C, I
from interval_label_validation import buffer_filter, commit, merge, minus, start_parts


def fraction_json(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: fraction_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [fraction_json(v) for v in value]
    return value


def contacts():
    rows = [
        ("c1", "X", "B", 2, 3, 0), ("c2", "B", "D", 6, 7, 1),
        ("c3", "A", "B", 1, 2, 0), ("c4", "A", "B", 7, 9, 0),
        ("c5", "B", "D", 10, 11, 1), ("c6", "A", "C", 1, 2, 1),
        ("c7", "C", "D", 4, 5, 0), ("c8", "C", "D", 2, 3, 0),
    ]
    return [C(cid, u, v, F(a), F(b), F(4), F(delta), ())
            for cid, u, v, a, b, delta in rows]


def trace_search(P):
    """Mirror the candidate control flow and check the final result against it."""
    outgoing, reached, queue, events, names = {}, {}, [], [], {}
    for c in P.cs:
        outgoing.setdefault(c.u, []).append(c)

    def label_info(label):
        return dict(id=names[id(label)], contact=label.c.id, node=label.c.v,
                    start_intervals=label.I, key=label.key,
                    predecessor=names[id(label.pred)] if label.pred else "SOURCE")

    def snapshot():
        return [label_info(l) for _, _, l in sorted(queue)]

    def insert(c, parts, pred):
        previous = reached.get(c.id, [])
        new = minus(parts, previous)
        reached[c.id] = merge(previous + new)
        made = []
        for interval in new:
            key = interval[0] + P.S / c.r + c.d
            label = SL.L(c, [interval], pred, key)
            names[id(label)] = f"L{len(names) + 1}"
            heapq.heappush(queue, (key, len(names), label))
            made.append(label_info(label))
        return made

    for c in outgoing.get(P.src, []):
        before = snapshot()
        parts = SL.source_parts(P, c)
        made = insert(c, parts, None)
        events.append(dict(event="source", contact=c.id, starts=parts,
                           labels=made, q_before=before, q_after=snapshot()))
    while queue:
        before = snapshot()
        _, _, current = heapq.heappop(queue)
        events.append(dict(event="pop", label=label_info(current),
                           q_before=before, q_after=snapshot()))
        if current.c.v == P.dst:
            schedule = SL.backtrack(P, current)
            reference = SL.backtrack(P, SL.search(P))
            assert [(c.id, s) for c, s in schedule] == [(c.id, s) for c, s in reference]
            events.append(dict(event="goal", label=label_info(current), q_after=snapshot()))
            return schedule, events
        c1 = current.c
        for c2 in outgoing.get(c1.v, []):
            raw_head = max(c2.a, current.I[0][0] + c1.d + P.S / c1.r)
            raw_tail = min(c2.b - P.S / c2.r, P.T - P.S / c2.r - c2.d)
            parts = start_parts(P, c2, current.I[0][0] + c1.d + P.S / c1.r)
            feasible = buffer_filter(P, parts, current.I, c1, c2, True, EX=P.S / c1.r) if parts else []
            before = snapshot()
            made = insert(c2, feasible, current)
            reason = ("time_window" if raw_head > raw_tail else "booked_contact" if not parts
                      else "buffer" if not feasible else "accepted")
            events.append(dict(event="extend", predecessor=label_info(current), contact=c2.id,
                               head=raw_head, tail=raw_tail, starts=parts, feasible=feasible,
                               reason=reason, labels=made, q_before=before, q_after=snapshot()))
    return None, events


def ramp_value(t, left, right, size):
    """Independent of candidate ramp/occ/buffer_filter helpers."""
    if t <= left:
        return F(0)
    if t >= right:
        return size
    return size * (t - left) / (right - left)


def visit_load(visit, t, side="right"):
    size = visit["size"]
    if visit["source"]:
        active = t >= visit["g"] if side == "right" else t > visit["g"]
        received = size if active else F(0)
    else:
        received = ramp_value(t, visit["h"], visit["A"], size)
    if visit["destination"]:
        released = t >= visit["A"] if side == "right" else t > visit["A"]
        return F(0) if released else received
    return received - ramp_value(t, visit["s"], visit["f"], size)


def schedule_visits(P, schedule):
    visits = []
    previous = None
    for c, s in schedule:
        visits.append(dict(node=c.u, source=previous is None, destination=False,
                           size=P.S, g=P.g,
                           h=None if previous is None else previous[1] + previous[0].d,
                           A=P.g if previous is None else previous[1] + previous[0].d + P.S / previous[0].r,
                           s=s, f=s + P.S / c.r))
        previous = c, s
    c, s = schedule[-1]
    visits.append(dict(node=c.v, source=False, destination=True, size=P.S, g=P.g,
                       h=s+c.d, A=s+c.d+P.S/c.r, s=None, f=None))
    return visits


def validate(P, schedule, accepted_visits):
    previous = None
    for c, s in schedule:
        f = s + P.S / c.r
        assert c.a <= s and f <= c.b and f + c.d <= P.T
        assert not any(s < y and x < f for x, y in c.F)
        assert s >= (P.g if previous is None else previous[1]+previous[0].d+P.S/previous[0].r)
        assert c.u == (P.src if previous is None else previous[0].v)
        previous = c, s
    assert previous[0].v == P.dst
    all_visits = accepted_visits + schedule_visits(P, schedule)
    peaks = {}
    for node in {v["node"] for v in all_visits}:
        group = [v for v in all_visits if v["node"] == node]
        points = sorted({v[k] for v in group for k in ["g", "h", "A", "s", "f"] if v[k] is not None})
        # Each aggregate is affine between breakpoints; both event sides are checked.
        peak = max(sum((visit_load(v, t, side) for v in group), F(0))
                   for t in points for side in ["left", "right"])
        assert peak <= P.M, (node, peak)
        peaks[node] = peak
    return peaks


def grid_oracle(P, accepted_visits):
    """Small DAG-only fixture oracle at quarter-second resolution."""
    outgoing = {}
    for c in P.cs:
        outgoing.setdefault(c.u, []).append(c)
    found = []
    def walk(node, ready, route):
        if node == P.dst:
            try:
                validate(P, route, accepted_visits)
                found.append((ready, route))
            except AssertionError:
                pass
            return
        for c in outgoing.get(node, []):
            s = max(c.a, ready)
            while s + P.S/c.r <= c.b:
                if not any(s < y and x < s+P.S/c.r for x, y in c.F):
                    walk(c.v, s+P.S/c.r+c.d, route+[(c,s)])
                s += F(1,4)
    walk(P.src, P.g, [])
    return min((a for a, _ in found), default=None)


def run(output):
    P = I(contacts(), "X", "D", F(0), F(4), F(4), {}, F(12))
    accepted_visits, bundles = [], []
    for number, source, release, expected in [(1,"X",0,8),(2,"A",1,5)]:
        P = P._replace(src=source,g=F(release))
        schedule, trace = trace_search(P)
        assert schedule is not None
        arrival = schedule[-1][1]+P.S/schedule[-1][0].r+schedule[-1][0].d
        assert arrival == expected
        peaks = validate(P, schedule, accepted_visits)
        assert grid_oracle(P, accepted_visits) == arrival
        accepted_visits += schedule_visits(P, schedule)
        P = commit(P, schedule)  # Actual prototype: F plus intermediate-node O only.
        bundles.append(dict(bundle=number,source=source,release=F(release),arrival=arrival,
                            schedule=[dict(contact=c.id,start=s,finish=s+P.S/c.r,
                                           first_byte=s+c.d,arrival=s+P.S/c.r+c.d) for c,s in schedule],
                            trace=trace,independent_all_node_peaks=peaks,
                            reservations={c.id:list(c.F) for c in P.cs if c.F},background=P.O))
    payload = dict(source_ppt="1013.pptx",algorithm="store_forward/store_label.py at d8ade1c",
                   business_deadline=None, finite_contact_coverage_bound="12",
                   capacity_model="rate and unoccupied transmission intervals; no independent quota",
                   c7_volume_MB="4",size_MB="4",buffer_MB="4",bundles=bundles,
                   checks=dict(candidate_trace_parity=True,quarter_second_fixture_oracle=True,
                               independent_source_transit_destination_buffer=True),
                   limitations=["No general correctness proof", "Not a research-scale experiment",
                                "Prototype DestinationFilter and endpoint Commit remain incomplete"])
    output.mkdir(parents=True,exist_ok=True)
    (output/"walkthrough.json").write_text(json.dumps(fraction_json(payload),ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(dict(arrivals=[str(b["arrival"]) for b in bundles],
                          paths=[[x["contact"] for x in b["schedule"]] for b in bundles],
                          checks=payload["checks"],output=str(output)),ensure_ascii=False))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("output/ppt_store_forward_20261103"))
    run(parser.parse_args().output)
