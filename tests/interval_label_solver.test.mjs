// node tests/interval_label_solver.test.mjs [參照 JSON]
import { readFileSync } from 'node:fs';
import { parseInstance, solve } from '../web/interval-label/solver.mjs';
const ref = JSON.parse(readFileSync(process.argv[2] || new URL('./data/interval_label_reference.json', import.meta.url)));
let bad = 0;
for (const c of ref.cases) {
  const r = solve(parseInstance(c.instance));
  const key = r.goal ? String(r.goal.key) : null;
  const reach = Object.fromEntries(Object.entries(r.reached).map(([k, v]) => [k, v.map(([a, b]) => [String(a), String(b)])]));
  const sch = r.sch ? r.sch.map(({ c: x, s }) => [x.id, String(s)]) : null;
  if (key !== c.arrival || JSON.stringify(sch) !== JSON.stringify(c.schedule)) { bad++; console.log('DIFF', c.name, key, c.arrival, sch, c.schedule); }
  if (r.valid === false) { bad++; console.log('INVALID', c.name); }
  c.checkedReach = reach;
}
console.log(`cases=${ref.cases.length} differ=${bad}`);
process.exit(bad ? 1 : 0);
