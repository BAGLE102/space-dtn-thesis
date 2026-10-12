// 重播狀態只由走到目前的 trace 推導；不能使用結果檔的最終 active/processed 值。
export const num = x => typeof x === 'number' ? x : String(x).split('/').map(Number).reduce((a,b)=>a/b);
export function frames(record) {
  const out = [{event:'INIT', queue_before:[], queue_after:record.labels.L0 ? ['L0'] : []}];
  for (const e of record.trace) {
    if (e.event === 'EXTEND') {
      out.push({...e, phase:'CHECK', queue_after:e.queue_before});
      if (e.new_label) out.push({...e, phase:'DECIDE'});
    } else out.push(e);
  }
  if (record.status === 'ACCEPTED') out.push({event:'COMMIT', selected:out.at(-1).selected, queue_before:out.at(-1).queue_after, queue_after:[]});
  return out;
}
export function stateAt(record, steps, index) {
  const labels = {};
  if (record.labels.L0) labels.L0 = {...record.labels.L0, active:true, status:'待展開'};
  for (const e of steps.slice(0,index+1)) {
    if (e.event === 'POP' && labels[e.selected]) labels[e.selected].status = '已取出';
    if (e.event === 'GOAL' && labels[e.selected]) labels[e.selected].status = '選定目的地';
    if (e.phase === 'DECIDE') {
      labels[e.new_label] = {...record.labels[e.new_label], active:!e.dominated_by?.length,
        status:e.dominated_by?.length ? '被支配' : '待展開'};
      for (const id of e.removed || []) {labels[id].active=false; labels[id].status='被支配';}
    }
  }
  return {labels, queue:steps[index].queue_after || []};
}
export function chain(labels, id) {
  const result=[], seen=new Set();
  while (id && labels[id]) {
    if (seen.has(id)) throw Error('前驅鏈出現循環');
    seen.add(id); result.unshift(labels[id]); id=labels[id].pred;
  }
  return result;
}
export function curveValue(curve,t) {
  return Math.max(0,...curve.filter(s=>num(s[0])<=t && t<=num(s[1])).map(s=>{
    const [a,b,y,z]=s.map(num);return a===b?y:y+(z-y)*(t-a)/(b-a);
  }));
}
