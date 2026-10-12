import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {num,frames,stateAt,chain,curveValue} from './model.mjs';
assert.equal(num('4'),4);
assert.equal(num('1/2'),0.5);
const ppt=JSON.parse(readFileSync(new URL('./data/ppt.json',import.meta.url)));
for(const r of ppt.records){
 const fs=frames(r);
 assert.deepEqual(Object.keys(stateAt(r,fs,0).labels),['L0']);
 for(let i=0;i<fs.length;i++){
  const e=fs[i],s=stateAt(r,fs,i);
  for(const id of s.queue)assert.ok(s.labels[id]);
  if(e.phase==='CHECK' && e.new_label)assert.equal(s.labels[e.new_label],undefined);
  if(e.phase==='DECIDE'){
   assert.deepEqual(s.queue,e.queue_after);
   assert.equal(s.labels[e.new_label].active,!e.dominated_by?.length);
  }
  for(const id of Object.keys(s.labels))chain(s.labels,id);
 }
 const goal=fs.findIndex(e=>e.event==='GOAL');
 assert.deepEqual(chain(stateAt(r,fs,goal).labels,fs[goal].selected).filter(l=>l.c).map(l=>[l.c,l.s]),r.hops);
}
const late=JSON.parse(readFileSync(new URL('./data/later-start.json',import.meta.url)));
assert.deepEqual(frames(late.records[0]).filter(e=>e.phase==='CHECK').map(e=>e.s),['0','1','2','3']);
assert.equal(curveValue([[1,2,0,4],[2,6,4,4]],2),4);
console.log('Website state, predecessor, enumeration and curve checks passed.');
