"""Check v1.2 slide claims against the latest code and saved validation record.

This checks the two-slide fixture and refines only the six off-grid cases.
It does not rerun the 3,000-case experiment or prove general correctness.
"""
from collections import Counter
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/experiments/dtn_validation"))
from dtn import ours, oracle, topology, validate as V
from dtn.model import Contact, Problem, arrival


def main():
    record = ROOT / "output/dtn_validation_20261103/validation.jsonl"
    rows = [json.loads(line) for line in record.read_text().splitlines() if line]
    counts = Counter(row["result"] for row in rows)
    assert len(rows) == 5961 and len({r["case"] for r in rows}) == 3000
    assert counts == {"both_none": 3705, "same": 2250, "earlier": 6}
    assert not any(r["replay_ok"] is False for r in rows)
    earlier = {(r["case"], r["bundle"]) for r in rows if r["result"] == "earlier"}
    checks = []
    for seed in sorted({seed for seed, _ in earlier}):
        P, bundles = topology.small_case(seed)
        for idx, (src, dst, g) in enumerate(bundles):
            P = P._replace(src=src, dst=dst, g=g)
            sch = ours.plan(P)
            if sch:
                assert V.validate(P, sch), (seed, idx)
            if (seed, idx) in earlier:
                coarse = oracle.earliest(P, F(1, 16))
                fine = oracle.earliest(P, F(1, 48))
                actual = arrival(P, sch)
                assert actual < coarse and actual == fine, (seed, idx)
                checks.append(dict(case=seed, bundle=idx,
                                   ours=str(actual), grid_16=str(coarse),
                                   grid_48=str(fine), replay_ok=True))
            if sch:
                P = V.commit(P, sch)

    rows_c = [("c1", "X", "B", 2, 3, 0), ("c2", "B", "D", 6, 7, 1),
              ("c3", "A", "B", 1, 2, 0), ("c4", "A", "B", 7, 9, 0),
              ("c5", "B", "D", 10, 11, 1), ("c6", "A", "C", 1, 2, 1),
              ("c7", "C", "D", 4, 5, 0), ("c8", "C", "D", 2, 3, 0)]
    cs = [Contact(cid, u, v, F(a), F(b), F(4), F(dl), ())
          for cid, u, v, a, b, dl in rows_c]
    P = Problem(cs, "X", "D", F(0), F(4), F(4), {}, F(12))
    fixture = []
    for src, g, expected, ids in [("X", 0, 8, ["c1", "c2"]),
                                   ("A", 1, 5, ["c6", "c7"])]:
        P = P._replace(src=src, g=F(g))
        sch = ours.plan(P)
        assert V.validate(P, sch)
        assert arrival(P, sch) == oracle.earliest(P, F(1, 4)) == expected
        assert [c.id for c, _ in sch] == ids
        P = V.commit(P, sch)
        assert src in P.O and "D" in P.O
        fixture.append(dict(source=src, arrival=expected,
                            schedule=[dict(contact=c.id, start=str(s)) for c, s in sch],
                            committed_nodes=sorted(P.O)))
    result = dict(algorithm_reference="67db7a2", saved_record=str(record.relative_to(ROOT)),
                  cases=3000, queries=len(rows), results=dict(counts),
                  replay_failures=0, refined_off_grid=checks, fixture=fixture,
                  limitation="Saved record counted, not fully rerun; six cases refined; no general proof.")
    out = ROOT / "output/ppt_store_forward_20261103/v1_2_source_checks.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps(dict(cases=3000, queries=len(rows), results=dict(counts),
                         refined_cases=len(checks), fixture_arrivals=[8, 5],
                         output=str(out.relative_to(ROOT))), ensure_ascii=False))


if __name__ == "__main__":
    main()
