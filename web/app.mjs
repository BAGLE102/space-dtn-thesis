import {num,frames,stateAt,chain,curveValue} from './model.mjs?v=1';
const $=id=>document.getElementById(id);
const esc=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=x=>x==null?'—':Number(num(x).toFixed(3)).toString();
let cases=[],ci=0,bi=0,index=0,steps=[],timer=null,filter=null,highlight=null;
const code=[
 'if source buffer cannot hold S at g: return NO_ROUTE_ON_GRID',
 'Q ← {L0}; Labels ← {L0}; solution ← none',
 'while Q is not empty:',
 '  L ← ExtractMin(Q, arrival time)',
 '  if L is inactive: continue',
 '  if node(L) = destination: solution ← TraceBack(L); break',
 '  for each outgoing contact c:',
 '    if route_usage(L,c) + S > R[c]: continue',
 '    first ← max(A(L), start(c)); last ← end(c) − S/r(c)',
 '    for s = first to last, step Δ:',
 '      f ← s + S/r(c); h ← s + δ(c); Anew ← f + δ(c)',
 '      if time or sender/receiver buffer check fails: continue',
 '      N ← (c, Anew, s, predecessor=L)',
 '      compare N with active labels at the same node',
 '      if an existing label dominates N: discard N',
 '      else: invalidate dominated labels; insert N into Q',
 'if solution is none: return NO_ROUTE_ON_GRID',
 'if independent validation fails: stop and preserve case',
 'commit capacity and buffer reservations; return solution'
];
$('pseudo').innerHTML=code.map((s,i)=>`<li data-line="${i}">${esc(s)}</li>`).join('');
function stage(e){return e.phase==='CHECK'?'延伸檢查':e.phase==='DECIDE'?'支配比較與入隊':({INIT:'初始化',POP:'取出 Label',STALE:'略過失效 Label',CONTACT_QUOTA_FAIL:'容量不足',CONTACT_TIME_FAIL:'沒有可用開始時間',GOAL:'取出目的地並回溯',EXHAUSTED:'搜尋結束',SOURCE_FAIL:'來源 Buffer 不足',COMMIT:'驗證後預約資源'}[e.event]||e.event);}
function lines(e){if(e.phase==='CHECK')return[9,10,11];if(e.phase==='DECIDE')return[12,13,e.dominated_by?.length?14:15];return {INIT:[1],POP:[3],STALE:[4],CONTACT_QUOTA_FAIL:[7],CONTACT_TIME_FAIL:[8],GOAL:[5],EXHAUSTED:[16],COMMIT:[17,18],SOURCE_FAIL:[0]}[e.event]||[];}
function describe(e,r,labels){
 const label=labels[e.selected];
 if(e.phase==='CHECK')return `從 ${e.selected}（${label?.node}，完整抵達 ${fmt(label?.A)} 秒）嘗試 ${e.contact}，開始時間 s=${fmt(e.s)} 秒。最後 byte 於 ${fmt(e.f)} 秒送出，於 ${fmt(e.arrival)} 秒完整抵達。${e.reason==='PASS'?'本次延伸可行，下一步進行 Label 建立與支配比較。':'這個開始時間不可行；仍會繼續嘗試此 Contact 後面的格點。'}`;
 if(e.phase==='DECIDE')return e.dominated_by?.length?`建立候選 ${e.new_label} 後，由 ${e.dominated_by.join('、')} 支配，因此不加入 Q。${e.dominated_by.map(k=>`${k} 抵達 ${fmt(labels[k].A)} 秒，能持包等到 ${fmt(labels[e.new_label].A)} 秒；各 Contact 用量也不更多。`).join(' ')}`:`保留 ${e.new_label} 並加入 Q。${e.removed?.length?'將 '+e.removed.join('、')+' 標成失效，前驅紀錄仍保留。':'目前沒有被它取代的既有 Label。'}`;
 if(e.event==='POP')return `依完整抵達時間從 Q 取出 ${e.selected}，目前節點為 ${label?.node}。接下來逐一檢查此節點的 outgoing contacts，再枚舉各個開始時間；此時尚未選定最終路徑。`;
 if(e.event==='GOAL')return `取出有效目的地 ${e.selected}，完整抵達時間 ${fmt(r.arrival)} 秒。沿 pred 回溯，取得 ${r.hops.map(h=>h[0]).join(' → ')||'零跳路徑'}。接下來才做完整路徑驗證與資源預約。`;
 if(e.event==='COMMIT')return `路徑已通過獨立完整排程檢查。扣除所選 Contact 的 ${fmt(r.bundle.size)} MB 容量並預約沿途 Buffer，下一個 Bundle 使用更新後的狀態。其餘 Q 候選不再搜尋。`;
 if(e.event==='CONTACT_QUOTA_FAIL')return `${e.contact} 剩餘容量 ${fmt(e.quota)} MB；此路徑已用 ${fmt(e.used)} MB，再傳整包 ${fmt(r.bundle.size)} MB 會超過容量，因此略過整個 Contact。`;
 if(e.event==='CONTACT_TIME_FAIL')return `${e.contact} 最早可開始 ${fmt(e.earliest)} 秒，但最晚必須 ${fmt(e.latest)} 秒開始，沒有可行的開始時間。`;
 if(e.event==='STALE')return `${e.selected} 已被其他 Label 支配，從 Q 取出時略過；紀錄保留供回溯使用。`;
 if(e.event==='EXHAUSTED')return 'Q 已耗盡。在目前時間格點、容量與 Buffer 模型下，沒有找到可行路徑。';
 if(e.event==='SOURCE_FAIL')return 'Bundle 產生時，來源節點的既有占用加上本包超過 Buffer 上限，未建立來源 Label。';
 return `本次處理 ${r.bundle.id}：${r.bundle.source} → ${r.bundle.dest}，產生時間 ${fmt(r.bundle.g)} 秒，大小 ${fmt(r.bundle.size)} MB。建立來源 L0；尚未預約本包的任何 Contact。`;
}
// SVG 僅顯示實際資料；接收／送出曲線沿用 Python trace 的時間與既有占用。
function graph(c,r,e,labels,id){
 const nodes=Object.keys(c.buffers), preset={X:[65,65],A:[65,270],B:[265,100],C:[265,285],D:[490,185]};
 const pos=nodes.length===5 && nodes.every(n=>preset[n])?preset:Object.fromEntries(nodes.map((n,i)=>[n,[70+(i%3)*205,70+Math.floor(i/3)*100]]));
 const height=Math.max(340,Math.ceil(nodes.length/3)*100+40);$('graph').setAttribute('viewBox',`0 0 560 ${height}`);
 const route=chain(labels,id).map(l=>l.c),prior=cases[ci].records.slice(0,bi).flatMap(q=>q.hops.map(h=>h[0]));
 const goal=e.event==='GOAL'||e.event==='COMMIT';
 let html='<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="context-stroke"/></marker></defs>';
 c.contacts.forEach((contact,i)=>{
   const [x,y]=pos[contact.u],[xx,yy]=pos[contact.v],dx=xx-x,dy=yy-y,len=Math.hypot(dx,dy),nx=-dy/len,ny=dx/len;
   const peers=c.contacts.filter(k=>k.u===contact.u&&k.v===contact.v),offset=(peers.findIndex(k=>k.id===contact.id)-(peers.length-1)/2)*46;
   const mx=(x+xx)/2+nx*offset,my=(y+yy)/2+ny*offset;
   const color=e.contact===contact.id?'#2469c5':route.includes(contact.id)?(goal?'#198158':'#2469c5'):prior.includes(contact.id)?'#c77920':'#ccd5e0';
   html+=`<path d="M${x+dx/len*24},${y+dy/len*24} Q${mx},${my} ${xx-dx/len*27},${yy-dy/len*27}" fill="none" stroke="${color}" stroke-width="${color==='#ccd5e0'?1.5:3}" marker-end="url(#arrow)"/><text x="${mx}" y="${my-10}" text-anchor="middle" fill="${color==='#ccd5e0'?'#7c899b':color}" font-size="14">${esc(contact.id)}</text><text x="${mx}" y="${my+7}" text-anchor="middle" fill="#6f7d90" font-size="10">[${fmt(contact.start)}, ${fmt(contact.end)}] 秒</text>`;
 });
 nodes.forEach(n=>{const [x,y]=pos[n];html+=`<g data-node="${esc(n)}" tabindex="0" role="button" aria-label="篩選節點 ${esc(n)}" style="cursor:pointer"><circle cx="${x}" cy="${y}" r="23" fill="${filter===n?'#e1edff':'white'}" stroke="${n===labels[e.selected]?.node?'#2469c5':'#344a67'}" stroke-width="3"/><text x="${x}" y="${y+6}" text-anchor="middle" font-size="19" fill="#233c5c">${esc(n)}</text></g>`;});
 $('graph').innerHTML=html;
 $('graph').querySelectorAll('[data-node]').forEach(g=>{g.onclick=()=>{filter=g.dataset.node;render();};g.onkeydown=ev=>{if(ev.key==='Enter'){filter=g.dataset.node;render();}};});
 const path=chain(labels,id);$('path').textContent=path.length?`${id}：${path.map(l=>l.c||'來源').join(' → ')}　｜　${fmt(path.at(-1).A)} 秒完整抵達`:'尚無候選路徑';
}
function buffers(c,r,e,labels){
 const contact=c.contacts.find(k=>k.id===e.contact);
 if(e.event!=='EXTEND'||!contact){$('buffers').innerHTML='<p class="hint">嘗試開始時間時，這裡顯示傳送端與接收端的占用曲線。</p>';return;}
 const S=num(r.bundle.size),a=num(labels[e.selected].A),s=num(e.s),f=num(e.f),h=num(e.h),arr=num(e.arrival),T=num(c.horizon);
 const plot=(node,own)=>{
  const bg=r.background[node]||[],limit=num(c.buffers[node]);
  const breaks=new Set([0,T,...own.flatMap(z=>z.slice(0,2)),...bg.flat(1).flatMap(z=>z.slice(0,2).map(num))]);
  // 在折點兩側取值，保留交付時的尖峰與釋放後的跳降；不把端點重複相加。
  const times=[...breaks].sort((a,b)=>a-b).flatMap(t=>[Math.max(0,t-1e-6),t,Math.min(T,t+1e-6)]);
  const values=times.map(t=>[t,bg.reduce((v,curve)=>v+curveValue(curve,t),0),curveValue(own,t)]);
  const ymax=Math.max(limit,...values.map(z=>z[1]+z[2]),1)*1.2;
  const X=t=>42+t/T*450,Y=v=>112-v/ymax*85;
  // 本次接收曲線只檢查到整包抵達；不畫抵達後的假釋放，後續等待留待下一跳。
  const lo=own[0][0],hi=own.at(-1)[1];
  const path=k=>(k===1?values:values.filter(v=>lo<=v[0]&&v[0]<=hi)).map((v,i)=>`${i?'L':'M'}${X(v[0])},${Y(k===3?v[1]+v[2]:v[k])}`).join(' ');
  return `<svg class="bufferplot" viewBox="0 0 530 145" role="img" aria-label="${esc(node)} Buffer 占用"><text x="5" y="15" font-size="13">${esc(node)} · 上限 ${fmt(limit)} MB</text><line x1="42" y1="112" x2="492" y2="112" stroke="#bbc7d6"/><line x1="42" y1="${Y(limit)}" x2="492" y2="${Y(limit)}" stroke="#8593a5" stroke-dasharray="4 4"/><path d="${path(1)}" fill="none" stroke="#c77920" stroke-width="2"/><path d="${path(2)}" fill="none" stroke="#2469c5" stroke-width="2"/><path d="${path(3)}" fill="none" stroke="#bd3646" stroke-width="2"/>${[0,T/4,T/2,T*3/4,T].map(t=>`<text x="${X(t)}" y="132" text-anchor="middle" font-size="11">${fmt(t)}</text>`).join('')}<text x="30" y="115" text-anchor="end" font-size="10">0</text><text x="30" y="${Y(limit)+4}" text-anchor="end" font-size="10">${fmt(limit)}</text></svg>`;
 };
 $('buffers').innerHTML=plot(contact.u,[[a,s,S,S],[s,f,S,0]])+plot(contact.v,[[h,arr,0,S]]);
}
function render(){
 const c=cases[ci],r=c.records[bi],e=steps[index],state=stateAt(r,steps,index),labels=state.labels;
 const id=highlight&&labels[highlight]?highlight:e.new_label&&labels[e.new_label]?e.new_label:e.selected||'L0';
 $('stage').textContent=stage(e);$('event').textContent=e.event+(e.phase?' / '+e.phase:'');
 $('count').textContent=`${index+1} / ${steps.length}`;$('position').value=index;$('position').max=steps.length-1;
 $('prev').disabled=$('first').disabled=index===0;$('next').disabled=$('last').disabled=index===steps.length-1;
 $('meta').textContent=`Δ=${fmt(c.delta)} 秒 · T=${fmt(c.horizon)} 秒 · 同模型檢查通過`;
 $('explanation').textContent=describe(e,r,labels);
 $('checks').innerHTML=e.event==='EXTEND'?[
  ['時間',e.temporal],['容量',e.quota],['傳送端峰值 '+fmt(e.sender_peak)+' / '+fmt(c.buffers[c.contacts.find(k=>k.id===e.contact).u])+' MB',num(e.sender_peak)<=num(c.buffers[c.contacts.find(k=>k.id===e.contact).u])],
  ['接收端峰值 '+fmt(e.receiver_peak)+' / '+fmt(c.buffers[c.contacts.find(k=>k.id===e.contact).v])+' MB',num(e.receiver_peak)<=num(c.buffers[c.contacts.find(k=>k.id===e.contact).v])]
 ].map(([t,ok])=>`<span class="check ${ok?'pass':'fail'}">${esc(t)} ${ok?'✓':'✕'}</span>`).join(''):'';
 $('pseudo').querySelectorAll('li').forEach((li,i)=>li.classList.toggle('active',lines(e).includes(i)));
 const chips=q=>q?.length?q.map(k=>`<button class="chip" data-label="${esc(k)}">${esc(k)} · A=${fmt(labels[k]?.A)}</button>`).join(''):'∅';
 $('before').innerHTML=chips(e.queue_before);$('after').innerHTML=chips(e.queue_after);
 $('labels').innerHTML=Object.values(labels).filter(l=>!filter||l.node===filter).map(l=>`<tr data-label="${esc(l.id)}" class="${l.id===id?'selected ':''}${l.active?'':'inactive'}"><td>${esc(l.id)}</td><td>${esc(l.node)}</td><td>${esc(l.c||'c⊥')}</td><td>${fmt(l.A)}</td><td>${fmt(l.s)}</td><td>${esc(l.pred||'∅')}</td><td>${esc(l.status)}</td></tr>`).join('');
 document.querySelectorAll('[data-label]').forEach(el=>el.onclick=()=>{highlight=el.dataset.label;render();});
 $('clearfilter').textContent=filter?`目前：${filter} · 顯示全部`:'顯示全部節點';
 const quota=e.event==='COMMIT'?r.quota_after:r.quota_before;
 $('contacts').innerHTML=c.contacts.map(k=>`<tr class="${k.id===e.contact?'selected':''}"><td>${esc(k.id)}</td><td>${esc(k.u)} → ${esc(k.v)}</td><td>[${fmt(k.start)}, ${fmt(k.end)}]</td><td>${fmt(k.rate)}</td><td>${fmt(k.delay)}</td><td>${fmt(quota[k.id])}</td></tr>`).join('');
 $('log').innerHTML=steps.slice(0,index+1).map((s,i)=>`<div class="logline ${i===index?'current':''}" data-step="${i}">${i+1}. ${esc(stage(s))} ${esc(s.selected||'')} ${esc(s.contact||'')}${s.s!=null?' · s='+fmt(s.s):''}${s.reason?' · '+esc(s.reason):''}</div>`).join('');
 $('log').querySelectorAll('[data-step]').forEach(el=>el.onclick=()=>move(Number(el.dataset.step)));
 graph(c,r,e,labels,id);buffers(c,r,e,labels);
}
function stop(){clearInterval(timer);timer=null;$('play').textContent='▶ 播放';}
function move(i){index=Math.max(0,Math.min(steps.length-1,i));highlight=null;render();if(index===steps.length-1)stop();}
function selectBundle(){stop();bi=Number($('bundle').value);steps=frames(cases[ci].records[bi]);filter=null;move(0);}
function selectCase(){ci=Number($('case').value);$('bundle').innerHTML=cases[ci].records.map((r,i)=>`<option value="${i}">${esc(r.bundle.id)} · ${esc(r.bundle.source)} → ${esc(r.bundle.dest)} · ${fmt(r.bundle.size)} MB</option>`).join('');selectBundle();}
$('case').onchange=selectCase;$('bundle').onchange=selectBundle;
$('first').onclick=()=>{stop();move(0);};$('last').onclick=()=>{stop();move(steps.length-1);};$('prev').onclick=()=>{stop();move(index-1);};$('next').onclick=()=>{stop();move(index+1);};
$('position').oninput=()=>{stop();move(Number($('position').value));};
$('play').onclick=()=>{if(timer){stop();return;}if(index===steps.length-1)move(0);$('play').textContent='Ⅱ 暫停';timer=setInterval(()=>move(index+1),Number($('speed').value));};
$('speed').onchange=()=>{if(timer){stop();$('play').click();}};
$('clearfilter').onclick=()=>{filter=null;render();};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(t=>t.classList.toggle('on',t===b));$('pseudo').hidden=b.dataset.tab!=='pseudo';$('log').hidden=b.dataset.tab!=='log';});
document.addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON'].includes(e.target.tagName))return;if(e.key==='ArrowRight'){stop();move(index+1);}if(e.key==='ArrowLeft'){stop();move(index-1);}});
$('upload').onclick=()=>$('file').click();
// 匯入僅讀取資料；使用 textContent/HTML escaping，匯入檔不會執行腳本。
$('file').onchange=async()=>{
 try{const file=$('file').files[0];if(!file)return;if(file.size>5e6)throw Error('檔案需小於 5 MB');const c=JSON.parse(await file.text());
  if(!c.verified||!Array.isArray(c.contacts)||!Array.isArray(c.records)||!c.records.length||!c.buffers||num(c.horizon)<=0)throw Error('請使用 export_website 匯出的重播 JSON');
  for(const r of c.records){if(!r.labels||!Array.isArray(r.trace)||!r.quota_before||!r.background)throw Error('缺少 Label、trace 或資源資料');for(const l of Object.values(r.labels)){if(l.pred&&!r.labels[l.pred])throw Error('缺少前驅 Label');chain(r.labels,l.id);}for(const e of r.trace){for(const id of [...(e.queue_before||[]),...(e.queue_after||[])])if(!r.labels[id])throw Error('Q 引用不存在的 Label');}}
  cases.push(c);$('case').add(new Option(c.title,cases.length-1));$('case').value=cases.length-1;selectCase();$('error').textContent='匯入完成。「已驗證」標記來自匯出檔，本頁不會重新執行驗證。';
 }catch(err){$('error').textContent='匯入失敗：'+err.message;}
};
try{cases=await Promise.all(['ppt','later-start'].map(n=>fetch(`data/${n}.json`).then(r=>{if(!r.ok)throw Error('案例讀取失敗');return r.json();})));$('case').innerHTML=cases.map((c,i)=>`<option value="${i}">${esc(c.title)}</option>`).join('');selectCase();}catch(err){$('error').textContent=err.message;}
