import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
const runtimeModules=process.env.RUNTIME_NODE_MODULES;
if (!runtimeModules) throw new Error('Set RUNTIME_NODE_MODULES to the bundled Node packages directory.');
const requireRuntime=createRequire(path.join(runtimeModules,'package.json'));
const {FileBlob,PresentationFile}=await import(pathToFileURL(requireRuntime.resolve('@oai/artifact-tool')));

const ROOT=path.resolve('.');
const BUILD=path.join(ROOT,'.codex-ppt-build/1103_store_forward');
const SKILL=process.env.PRESENTATIONS_SKILL_DIR;
if (!SKILL) throw new Error('Set PRESENTATIONS_SKILL_DIR to the installed Presentations skill directory.');
const { applyPresentationChartFont }=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const SOURCE=process.argv[2] || 'F:/1013.pptx';
const FONT='DFKai-SB';
const C={blue:'#3932A8',green:'#187A3E',orange:'#CC6900',red:'#C52327',ink:'#222222',gray:'#747474',light:'#D8D8DF',faint:'#F2F1F7',white:'#FFFFFF'};
const data=JSON.parse(await fs.readFile(path.join(ROOT,'output/ppt_store_forward_20261103/walkthrough.json'),'utf8'));
const topologyGeometry=JSON.parse(await fs.readFile(path.join(ROOT,'src/presentations/1013_topology_link_geometry.json'),'utf8'));
const p=await PresentationFile.importPptx(await FileBlob.load(SOURCE));
await fs.mkdir(path.join(BUILD,'final-preview'),{recursive:true});
const notes=[];
let seq=0;
function txt(sl,text,x,y,w=1100,h=40,size=28,color=C.ink,align='left') {
 const t=sl.shapes.add({geometry:'textbox',name:`text-${seq++}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 t.text=text;t.text.style={typeface:FONT,fontSize:size,color,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};return t;
}
function rect(sl,x,y,w,h,fill=C.white,line=C.blue,lw=1.4) {
 return sl.shapes.add({geometry:'rect',name:`diagram-${seq++}`,position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:lw}});
}
function line(sl,x1,y1,x2,y2,color=C.light,width=1.5,arrow=false) {
 return sl.shapes.add({geometry:'connector',kind:'straight',position:{left:Math.min(x1,x2),top:Math.min(y1,y2),width:Math.max(0.1,Math.abs(x2-x1)),height:Math.max(0.1,Math.abs(y2-y1)),verticalFlip:y2<y1,horizontalFlip:x2<x1},line:{fill:color,width},tail:{type:arrow?'triangle':'none',width:'sm',length:'sm'}});
}
function base(index,title,takeaway,note) {
 const s=p.slides.items[index-1];
 s.shapes.deleteAll();
 // The source's sole raster is the obsolete buffer chart; replace it with editable evidence.
 for (const image of [...s.images.items]) s.images.deleteById(image.id);
 for (const t of [...s.tables.items]) s.tables.deleteById(t.id);
 for (const c of [...s.charts.items]) s.charts.deleteById(c.id);
 txt(s,title,88,48,1110,78,50,C.blue);
 txt(s,takeaway,88,640,1110,40,23,C.blue);
 txt(s,String(index),605,689,70,22,16,C.gray,'center');
 const n=`${note}\n一句重點：${takeaway}\n方法來源：docs/store_forward_label_20261103.md；GitHub d8ade1c。\n案例資料：output/ppt_store_forward_20261103/walkthrough.json。\n本簡報呈現候選方法，尚無一般正確性證明。`;
 s.speakerNotes.text=n;notes.push({slide:index,title,takeaway,notes:n});return s;
}
function bullets(s,rows,x=90,y=162,w=1090,size=30,gap=72) {
 rows.forEach((r,i)=>txt(s,`${i+1}. ${r}`,x,y+i*gap,w,gap-10,size));
}
function table(s,values,x,y,w,h,widths,size=25) {
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 t.borders.assign({fill:'#A4A2B7',width:1,style:'solid'});
 for(let r=0;r<values.length;r++) for(let c=0;c<values[r].length;c++) {
  const cell=t.getCell(r,c);cell.fill=r===0?C.faint:C.white;
  cell.text.style={typeface:FONT,fontSize:size,color:r===0?C.blue:C.ink,insets:8,verticalAlignment:'middle',alignment:'left'};
 }
 return t;
}
function graph(s,active={},focus=null) {
 const pos={X:[128,211],A:[128,405],B:[330,248],C:[330,446],D:[546,339]};
 const es=[['c1','X','B','[2,3]'],['c2','B','D','[6,7]'],['c3','A','B','[1,2]'],['c4','A','B','[7,9]'],
 ['c5','B','D','[10,11]'],['c6','A','C','[1,2]'],['c7','C','D','[4,5]'],['c8','C','D','[2,3]']];
 // Reuse the original three-point polylines; morph only for the existing node positions.
 const morph=(point,u,v)=>{
  const a=topologyGeometry.original_node_centers[u],b=topologyGeometry.original_node_centers[v];
  const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)));
  return [point[0]+(1-t)*(pos[u][0]-a[0])+t*(pos[v][0]-b[0]),point[1]+(1-t)*(pos[u][1]-a[1])+t*(pos[v][1]-b[1])];
 };
 const polyline=(points,color,width,name)=>{
  const left=Math.min(...points.map(q=>q[0])),top=Math.min(...points.map(q=>q[1]));
  const widthPx=Math.max(.1,Math.max(...points.map(q=>q[0]))-left),heightPx=Math.max(.1,Math.max(...points.map(q=>q[1]))-top);
  s.shapes.add({geometry:'custom',name,position:{left,top,width:widthPx,height:heightPx},fill:'none',line:{fill:color,width},
   customPaths:[{width:widthPx,height:heightPx,commands:points.map((q,i)=>({[i?'lineTo':'moveTo']:{x:q[0]-left,y:q[1]-top}}))}]});
 };
 for(const e of [...es.filter(e=>!active[e[0]]),...es.filter(e=>active[e[0]])]) {
  const [id,u,v]=e,col=active[id]||C.light,lw=active[id]?3.8:1.7;
  const points=topologyGeometry.links[id].points.map(q=>morph(q,u,v));
  const bend=points[1],end=pos[v],len=Math.hypot(end[0]-bend[0],end[1]-bend[1]);
  const d=[(end[0]-bend[0])/len,(end[1]-bend[1])/len],tip=[end[0]-d[0]*27.5,end[1]-d[1]*27.5];
  points[2]=tip;polyline(points,col,lw,`topology-${id}-polyline`);
  const back=[tip[0]-d[0]*10,tip[1]-d[1]*10];
  polyline([[back[0]-d[1]*4,back[1]+d[0]*4],tip,[back[0]+d[1]*4,back[1]-d[0]*4]],col,lw,`topology-${id}-arrow`);
 }
 // Nodes cover the source-center sections just as in the supplied reference.
 for(const [n,[x,y]]of Object.entries(pos)) {
  s.shapes.add({geometry:'ellipse',position:{left:x-26,top:y-26,width:52,height:52},fill:C.white,line:{fill:n===focus?C.green:C.blue,width:2.7}});
  txt(s,n,x-22,y-25,44,52,36,n===focus?C.green:C.blue,'center');
 }
 for(const [id,u,v,win]of es) {
  const [x,y]=morph(topologyGeometry.links[id].label_center_top,u,v),col=active[id]||'#9B9AA6';
  txt(s,id,x-29,y,58,30,25,col,'center');
  txt(s,win,x-38,y+26,76,24,16,col,'center');
 }
}
function qline(q) {
 if(!q||!q.length)return '[]';
 const labels=q.map(l=>`${l.id}=(${l.contact},[${l.start_intervals[0].join(',')}],${l.predecessor}), key=${l.key}`);
 // Show the complete mathematical Label; key is a derived queue priority outside its tuple.
 return '[ '+labels.map((label,i)=>`${i?(i%2===0?'\n   →   ':'   →   '):''}${label}`).join('')+' ]';
}
function queue(s,before,after,comment='') {
 txt(s,'Q 原本',88,530,110,36,25,C.gray);txt(s,typeof before==='string'?before:qline(before),205,530,1000,52,21,C.gray);
 txt(s,'Q 更新',88,584,110,36,25,C.blue);txt(s,typeof after==='string'?after:qline(after),205,584,1000,50,21,C.blue);
 if(comment)txt(s,comment,650,474,550,40,23,C.green);
}
function timeline(s,rows,{x=765,y=205,w=420,min=0,max=12}={}) {
 const xx=t=>x+(t-min)/(max-min)*w;
 for(let i=0;i<rows.length;i++) {
  const r=rows[i],yy=y+i*65;
  txt(s,r.label,x-135,yy-5,128,40,24,C.gray);
  line(s,x,yy+12,x+w,yy+12,C.light,1);
  for(const b of r.bars)rect(s,xx(b[0]),yy,Math.max(1,xx(b[1])-xx(b[0])),24,b[2]||C.green,b[2]||C.green,0);
 }
 const yb=y+rows.length*65+8;line(s,x,yb,x+w,yb,C.gray,1.3);
 const step=max-min<=5?1:2;
 for(let t=min;t<=max;t+=step){line(s,xx(t),yb,xx(t),yb+5,C.gray,1);txt(s,String(t),xx(t)-16,yb+9,35,27,19,C.gray,'center');}
 txt(s,'秒',x+w+28,yb+10,35,28,19,C.gray);
}
function chart(s,series,{x=655,y=210,w=540,h=265,max=4,title='占用量（MB）'}={}) {
 const chart=s.charts.add('scatter',{position:{left:x,top:y,width:w,height:h},hasLegend:true,
  legend:{position:'top',textStyle:{fontSize:17,typeface:FONT}},scatterOptions:{style:'line'},
  // Buffer ramps and holds are piecewise linear; smoothing would invent intermediate occupancy.
  series:series.map(o=>({name:o.name,xValues:o.points.map(z=>z[0]),values:o.points.map(z=>z[1]),smooth:false,line:{fill:o.color,width:o.width||2.8,style:o.dash?'dashed':'solid'},marker:{symbol:'none'}})),
  xAxis:{title:'時間（秒）',min:0,max:12,majorUnit:2,textStyle:{fontSize:18,typeface:FONT},majorGridlines:null},
  yAxis:{title,min:0,max,majorUnit:4,textStyle:{fontSize:18,typeface:FONT},majorGridlines:{fill:C.light,width:1}},
  chartFill:C.white,plotAreaFill:C.white});
 applyPresentationChartFont(chart,{fontFamily:FONT});return chart;
}
const B1=[[0,0],[2,0],[3,4],[6,4],[7,0],[12,0]];
const B2bad=[[0,0],[1,0],[2,4],[10,4],[11,0],[12,0]];
const C2=[[0,0],[2,0],[3,4],[4,4],[5,0],[12,0]];
const cap={name:'上限 4',points:[[0,4],[12,4]],color:C.gray,width:1.2};
function codes(s,lines,x=90,y=165,w=1100,size=25,gap=33){lines.forEach((t,i)=>txt(s,t,x,y+i*gap,w,gap+1,size,C.ink));}
const b1=data.bundles[0],b2=data.bundles[1];
let s;

s=base(1,'新版流程：區間 Label 延伸','保留整段可行起送時間；實際起送時刻在回溯時選定。','本次沿用 1013 的拓樸與逐步講解。方法是 store-and-forward：收完整包才轉送。以連續區間取代逐秒枚舉，不再對每個 s 建立 Label。每個連通可行區間是一個 Label；此處的移除已達集合不等同舊版同節點較早抵達支配。');
const flow=[['取出 Label','(c, I, pred)'],['選下一跳','完整收完才轉'],['求起送區間','扣除既有預約'],['檢查 Buffer','切出可行區間'],['更新 Reached','新區間加入 Q']];
flow.forEach(([a,b],i)=>{const x=90+i*230;rect(s,x,235,198,130,C.white,C.blue);txt(s,a,x+12,257,174,45,29,C.blue,'center');txt(s,b,x+10,310,178,45,23,C.ink,'center');if(i<4)line(s,x+199,301,x+228,301,C.blue,2,true);});
txt(s,'抵達目的地 → 沿 pred 回溯 → 驗證排程 → 提交資源',130,450,1040,58,34,C.green,'center');
txt(s,'候選方法｜store-and-forward｜無獨立配額',130,530,1040,40,25,C.gray,'center');

s=base(2,'研究環境：中央規劃、節點執行','上一包接受並預約後，下一包才使用更新後的資源搜尋。','中央端知道 contact plan 與已接受 bundles 的傳送時段和背景占用；這是固定已知預約的理想規劃模型，非分散式即時共識。Bundle 規劃順序固定，不保證多包整體最佳。節點依中央產生的排程執行 store-and-forward。');
for(const [x,head,body]of [[90,'輸入','Contact plan\nBundle requests'],[485,'中央規劃器','路由搜尋、時間選擇\n驗證、資源預約'],[915,'相關節點','保存完整 bundle\n依指定時段轉送']]){rect(s,x,210,x===485?325:280,175,C.white,C.blue);txt(s,head,x+20,230,x===485?285:240,50,32,C.blue,'center');txt(s,body,x+20,295,x===485?285:240,80,27,C.ink,'center');}
line(s,371,296,482,296,C.blue,2,true);line(s,812,296,912,296,C.blue,2,true);
bullets(s,['F[c]：contact 已預約的傳送時段','O_n(t)：已接受 bundles 在節點 n 的占用曲線','傳輸容量由速率與剩餘時段決定，不另加 aggregate quota'],90,440,1110,28,54);

s=base(3,'Label 的完整定義','Label 記錄可達時間與前驅；實際時刻在回溯時決定。','L_i 的 i 是本次單包搜尋中的唯一編號，不是 contact 編號。數學狀態仍為 c、I、pred 三項；key 是可由它們與 bundle 大小計算的推導值，Python 的 namedtuple 另外快取 key，並非新增研究狀態。I 是沿該前驅鏈可達的連通起送區間，不代表可以任意搭配前驅的所有時間。選定 s 後 A(L,s)=s+d(c)+δ(c)。目前範例為閉區間，下界可取到；一般開區間仍未補完。SOURCE 是來源標記，程式用 None，不是假 contact 或另一個 Label。Q 只持有待展開 Label；子 Label 的 pred 引用保留前驅，移出 Q 不等於刪除前驅物件。');
txt(s,'L_i = (c(L_i), I(L_i), pred(L_i))',125,155,1050,58,38,C.blue,'center');
table(s,[['項目','定義'],['i','本次搜尋的 Label 唯一編號；與 contact 編號分開'],['c(L)','最後使用的 contact；目前節點為 receiver(c(L))'],['I(L)','沿此前驅鏈可達的起送時間區間；本例為閉區間'],['pred(L)','前驅 Label 的引用；來源用 SOURCE（程式為 None）'],['key(L)','推導值：lo(I(L)) + d(c(L)) + δ(c(L))']],95,225,1090,285,[190,900],25);
txt(s,'選定 s ∈ I(L) 後：A(L,s) = s + d(c(L)) + δ(c(L))',105,535,1090,43,29,C.green);
txt(s,'lo(I)：區間下界；d(c)=S/r(c)；key 不鎖定實際起送時刻。',105,589,1090,38,25,C.blue);

s=base(4,'固定拓樸與兩包需求','先規劃 X→D，再規劃 A→D；兩包皆為 4 MB。','沿用 1013 五節點八個 contacts。第一包 release g=0，第二包 g=1。規劃先後不是實際送達先後。新版移除獨立配額後，第二包可走 c6、c7，故結果改為第 5 秒到達。');
graph(s);txt(s,'第一包：X → D，g=0',650,178,560,45,33,C.orange);txt(s,'第二包：A → D，g=1',650,240,560,45,33,C.blue);
bullets(s,['g：產生時間；S=4 MB','r=4 MB/s，d=S/r=1 秒','M=4 MB（各節點 Buffer 上限）','無業務 deadline；此計畫涵蓋抵達至 12 秒'],650,320,550,26,63);

s=base(5,'Contact plan 與容量模型','c7 的時長 1 秒、速率 4 MB/s，故傳輸量為 4 MB。','資料逐項取自 1013：時間窗與傳播延遲不變。原稿額外設定 R[c7]=2 MB，但新版無此獨立配額。此處列出的是 rate×duration 的初始物理傳輸量；不代表多個分離時段可以拼成不分割 bundle。每跳仍須有連續長度 d 的空檔。');
table(s,[['Contact','方向','時窗 [a,b]（秒）','δ（秒）','初始量（MB）'],['c1','X→B','[2,3]','0','4'],['c2','B→D','[6,7]','1','4'],['c3','A→B','[1,2]','0','4'],['c4','A→B','[7,9]','0','8'],['c5','B→D','[10,11]','1','4'],['c6','A→C','[1,2]','1','4'],['c7','C→D','[4,5]','0','4'],['c8','C→D','[2,3]','0','4']],95,150,1090,428,[160,190,290,170,280],26);
txt(s,'新版變更：刪除舊版 c7 的 2 MB 獨立配額。',105,591,1090,38,28,C.red);

s=base(6,'傳送、抵達與 Buffer 占用','上一跳整包抵達後，下一跳才可起送：s2 ≥ A1。','a(c)、b(c) 是 contact 開始與結束；s 是起送；f 是發送完成；h 是第一個 byte 抵達；A 是最後一個 byte 抵達。傳播延遲 δ 與傳輸時間 d 不同。中繼占用為已收減已送，接收時上升、持有時固定、發送時下降。來源從 g 擁有整包；目的地交付時釋放。端點實作缺口列於最後一頁。');
table(s,[['符號','意義／公式'],['d(c)','整包傳輸時間 S/r(c)'],['f','發送完成：s+d(c)'],['h','第一個 byte 抵達：s+δ(c)'],['A','整包抵達：s+d(c)+δ(c)'],['O_n(t)、M_n','既有背景占用、節點 Buffer 上限']],95,157,1090,350,[230,860],28);
txt(s,'整次造訪都要滿足：O_n(t) + 已收(t) − 已送(t) ≤ M_n',105,543,1090,50,30,C.green);

s=base(7,'SourceRange：直接得到起送區間','c4 的 [7,8] 包含所有實數起送時間，不逐秒枚舉。','來源已在 g=1 備妥。c4 從 7 開到 9，d=1，沒有預約，故起送集合 [7,8]。例如 7.5 也在其中。此例沒有 deadline；若輸入 D*，Tail 再與 D*−d−δ 取較小值。實驗程式使用 T=12 是此有限 contact plan 的涵蓋上界，沒有額外排除本例任何完整抵達。');
txt(s,'Head = max(a(c), g)',110,166,1060,49,35,C.blue);txt(s,'Tail = b(c) − d(c)　（未設 deadline）',110,226,1060,49,35,C.blue);
timeline(s,[{label:'c4 窗口',bars:[[7,9,C.light]]},{label:'可行起送 I',bars:[[7,8,C.green]]}],{x:305,y:350,w:820,min:6,max:10});
txt(s,'g=1，d=1 → I=[7,8]；若 Head>Tail，回傳空集合。',110,570,1090,43,30,C.green);

s=base(8,'第一包：來源 X 建立 c1 Label','c1 只能在第 2 秒起送，最早完整抵達 B 的時間為 3。','初始化不再把虛擬 L0 放進 Q，而是對來源的 outgoing contacts 建立可行起送區間。X 從 0 等到 2，持有 4 MB；2 到 3 逐 byte 發送下降。來源檢查通過。此時尚未預約任何全域資源。');
graph(s,{c1:C.green},'B');txt(s,'c1：I=[2,2]，key=2+1+0=3',650,160,560,50,31,C.green);
timeline(s,[{label:'X 等待',bars:[[0,2,C.light]]},{label:'X 發送',bars:[[2,3,C.green]]},{label:'B 接收',bars:[[2,3,C.green]]}],{min:0,max:4});
queue(s,[],b1.trace[0].q_after,'L1 = (c1, [2,2], SOURCE)');

s=base(9,'第一包：從 B 延伸 c2、c5','取出 L1 並完成延伸；L2、L3 的 pred 仍指向 L1。','先從 Q 取出 L1，Q 暫時為空，再對 B 出發的 c2、c5 延伸。c2 起送集合 [6,6]，完整到 D 為 8；c5 為 [10,10]，完整到 D 為 12。B 占用最高 4 MB。L2.pred=L1、L3.pred=L1，所以 L1 雖然離開 Q，仍透過子 Label 的引用保留供回溯。這些是替代候選，搜尋期間不各自提交占用。');
graph(s,{c1:C.green,c2:C.green,c5:C.blue},'B');
timeline(s,[{label:'c2 發送',bars:[[6,7,C.green]]},{label:'D 接收',bars:[[7,8,C.green]]},{label:'c5 發送',bars:[[10,11,C.blue]]},{label:'D 接收',bars:[[11,12,C.blue]]}],{y:175,min:6,max:12});
queue(s,b1.trace[1].q_before,b1.trace[3].q_after);
txt(s,'取出 L1 後延伸；L2.pred=L1，L3.pred=L1',650,490,550,32,21,C.green);

s=base(10,'第一包：選取目的地並回溯','取出 key=8 的目的地 Label，回推出 c1 在 2、c2 在 6 起送。','本例先取出 c2 的目的地 Label，c5 的另一目的地 Label 尚在 Q 中。回溯先定末跳 s=6，再在 c1 的 [2,2] 內找不超過 6−0−1=5 的最大值，得到 2。未取出的候選不是因 dominance 刪除。本頁只說明候選控制流程，本方法的一般最優性仍待證明。');
for(const [x,head,body]of [[105,'SOURCE','X，g=0'],[485,'L1：c1','I=[2,2] → s=2'],[865,'L2：c2','I=[6,6] → s=6']]){rect(s,x,240,280,130,C.white,C.green);txt(s,head,x+12,260,256,44,32,C.green,'center');txt(s,body,x+12,318,256,40,27,C.ink,'center');}
line(s,385,305,480,305,C.green,2,true);line(s,765,305,860,305,C.green,2,true);
txt(s,'回溯：L2 → L1 → SOURCE；排程：c1[2,3)、c2[6,7)',110,430,1090,54,31,C.green);
queue(s,b1.trace[4].q_before,b1.trace[4].q_after,'完整抵達 D：6+1+1=8 秒');

s=base(11,'第一包：提交 F 與 B 的占用曲線','接受後才預約 c1[2,3)、c2[6,7)，並寫入 B 的占用。','本頁忠實呈現目前 Commit：contact 傳送預約加上中繼節點曲線。B 在 2 到 3 接收，3 到 6 持有，6 到 7 發送下降。來源與目的地提交仍未完成；本例另有獨立完整節點重放，不能把該核對器當成原型已補完。');
graph(s,{c1:C.orange,c2:C.orange},'B');chart(s,[{name:'第一包 B',points:B1,color:C.orange},cap]);
txt(s,'B：2～3 接收，3～6 等待，6～7 發送',650,478,560,42,24,C.orange);
txt(s,'F[c1]={[2,3)}；F[c2]={[6,7)}',100,549,1100,47,31,C.blue);

s=base(12,'第二包：來源 A 先建立 c3 Label','收到整包只代表這個前綴可達；能否等待要延伸時再檢查。','第二包 g=1。在 A 的 outgoing contacts 依輸入順序 c3、c4、c6 初始化。c3 只能於 1 起送，2 到 B。來源 A 的 Buffer 通過；B 在 1 到 2 的接收也可行，但接續 c5 時會因等待遇到背景占用而失敗。');
graph(s,{c1:C.orange,c2:C.orange,c3:C.blue},'B');txt(s,'c3：I=[1,1]，key=1+1+0=2',650,175,560,50,31,C.blue);
timeline(s,[{label:'A 發送',bars:[[1,2,C.blue]]},{label:'B 接收',bars:[[1,2,C.blue]]}],{min:0,max:4,y:285});
queue(s,b2.trace[0].q_before,b2.trace[0].q_after,'L1 = (c3, [1,1], SOURCE)');

s=base(13,'第二包：c4 用一個 Label 保留 [7,8]','不建立 s=7、8 的兩個 Label；整段時間一起保留。','c4 的可行起送集合為閉區間 [7,8]。建立一個 L2，key=7+1=8；s=7.5 仍保存在同一個 Label 中。此頁沒有刪除較晚起送時間，也沒有用較早抵達做同節點 dominance。');
graph(s,{c1:C.orange,c2:C.orange,c4:C.blue},'B');
timeline(s,[{label:'c4 窗口',bars:[[7,9,C.light]]},{label:'起送區間 I',bars:[[7,8,C.blue]]}],{min:6,max:10,y:245});
queue(s,b2.trace[1].q_before,b2.trace[1].q_after,'L2=(c4,[7,8],SOURCE)，key=8');

s=base(14,'第二包：c6 加入 Q，依 key 排序','取出順序由最早完整抵達時間決定，不依 contact 編號。','c6 在 1 到 2 發送，傳播延遲為 1，C 在 2 到 3 接收，故 key=3。初始化建立順序為 c3、c4、c6，但 Q 排序為 c3(key2)、c6(key3)、c4(key8)。每次僅延伸被取出 Label 所在節點的 outgoing contacts，不在全圖按 contact 開始時間逐條走。');
graph(s,{c1:C.orange,c2:C.orange,c6:C.blue},'C');
timeline(s,[{label:'A 發送',bars:[[1,2,C.blue]]},{label:'C 接收',bars:[[2,3,C.green]]}],{min:0,max:4,y:235});
queue(s,b2.trace[2].q_before,b2.trace[2].q_after,'L3：c6，[1,1]，key=3');

s=base(15,'取出 c3：c2 的唯一空檔已被預約','c2 的候選起送時間 {6} 被已有傳送預約排除。','取出 L1 代表目前前綴於 B 的可行抵達，並不是已選整條路。c2 的 d=1，原本只能 s=6；第一包預約 [6,7)，衝突起送區間為 (6−1,7)=(5,7)，剛好把 6 排除。因此是時段用完，不是另一個獨立配額判斷。');
graph(s,{c1:C.orange,c2:C.red,c3:C.blue},'B');
txt(s,'c2 原起送集合：[6,6]',650,180,550,47,31,C.ink);txt(s,'已有預約：[6,7)',650,246,550,47,31,C.orange);
txt(s,'排除起送時間：(5,7)',650,312,550,47,31,C.red);txt(s,'[6,6] − (5,7) = 空集合',650,392,550,58,31,C.red);
queue(s,b2.trace[3].q_before,b2.trace[4].q_after);

s=base(16,'取出 c3：等待 c5 會使 B 超限','第 3 秒：前包 4 MB＋本包 4 MB＝8 MB，拒絕此延伸。','c5 可於 10 起送，但 c3 只能在 1 起送，因此第二包於 2 完整到 B 後須持有到 10。既有第一包在 B 的占用從 2 到 3 上升，合計第 3 秒達 8。圖從 0 秒開始；第二包於 1 到 2 接收，不與第一包於 2 到 3 的接收誤畫成同時上升。只拒絕 c3→c5 這個延伸，不取消其他候選。');
graph(s,{c1:C.orange,c2:C.orange,c3:C.blue,c5:C.red},'B');
chart(s,[{name:'第一包',points:B1,color:C.orange},{name:'第二包候選',points:B2bad,color:C.blue,dash:true},{name:'合計',points:[[0,0],[1,0],[2,4],[3,8],[6,8],[7,4],[10,4],[11,0],[12,0]],color:C.red},cap],{max:8});
queue(s,b2.trace[5].q_before,b2.trace[5].q_after,'BufferFilter 輸出空集合');

s=base(17,'取出 c6：c7 可傳整包','C 在 3 收完，4 起送 c7，5 完整抵達 D。','c7 初始 rate×duration=4 MB，沒有舊版的獨立 2 MB 配額。本包在 C 的接收為 2 到 3，持有為 3 到 4，發送為 4 到 5，峰值 4。BufferFilter 保留起送集合 [4,4]，新增 L4，key=5。此頁先 c7 再 c8，依輸入 outgoing contacts 順序；不影響 Q 以 key 取最小的規則。');
graph(s,{c1:C.orange,c2:C.orange,c6:C.green,c7:C.green},'C');
timeline(s,[{label:'C 接收',bars:[[2,3,C.green]]},{label:'C 等待',bars:[[3,4,C.light]]},{label:'c7 發送',bars:[[4,5,C.green]]},{label:'D 接收',bars:[[4,5,C.green]]}],{min:1,max:6,y:175});
queue(s,b2.trace[6].q_before,b2.trace[7].q_after,'L4=(c7,[4,4],L3)，key=5');

s=base(18,'同一個 c6 Label：c8 已經來不及','Head=3、Tail=2，候選起送區間為空。','c8 在 2 到 3 開放，d=1，所以最晚 2 必須起送。C 在 3 才收完整包；store-and-forward 不允許於 2 邊收邊轉，故 c8 不能使用。c7 剛建立的 L4 仍在 Q，不因 c8 失敗而移除。');
graph(s,{c6:C.blue,c8:C.red,c7:C.green},'C');
timeline(s,[{label:'c8 窗口',bars:[[2,3,C.light]]},{label:'C 接收',bars:[[2,3,C.blue]]},{label:'最早發送',bars:[[3,4,C.red]]}],{min:1,max:5,y:205});
queue(s,b2.trace[8].q_before,b2.trace[8].q_after,'3 > 2 → 不建立新 Label');

s=base(19,'第二包：先取出 key=5 的目的地','L2 尚未展開；它不是被較早 Label 支配刪除。','Q 中是 c7 的 L4(key5)與 c4 的 L2(key8)。先取出 L4 後，搜尋按候選規則結束。不能把剩下候選稱為 dominated：只是本次不再探索。此固定案例的最早抵達另由獨立小例窮舉核對；一般方法的首次目的地最優性尚待證明。');
graph(s,{c6:C.green,c7:C.green},'D');
txt(s,'L4：c7，I=[4,4]，key=5',650,220,550,52,34,C.green);txt(s,'L2：c4，I=[7,8]，key=8',650,300,550,52,34,C.gray);
txt(s,'先取出目的地 L4 → 回溯實際排程',650,405,550,60,30,C.green);
queue(s,b2.trace[9].q_before,b2.trace[9].q_after);

s=base(20,'第二包：沿 pred 選定實際起送時間','結果為 c6 在 1 起送、c7 在 4 起送，D 於 5 收完整包。','先選末跳 c7 的起送時間 4。前驅 c6 的可用上界為 4−δ(c6)−d(c6)=4−1−1=2；c6 的 I=[1,1]，最大可用值就是 1。整包於 C 的抵達為 1+1+1=3，不晚於下一跳 4。沿 pred 不是倒著傳，而是由最後一跳決定前面實際採用的時間。');
for(const [x,a,b]of [[100,'SOURCE','A，g=1'],[485,'L3：c6','I=[1,1] → s=1'],[870,'L4：c7','I=[4,4] → s=4']]){rect(s,x,225,280,145,C.white,C.green);txt(s,a,x+12,247,256,45,32,C.green,'center');txt(s,b,x+12,309,256,47,27,C.ink,'center');}
line(s,381,298,482,298,C.green,2,true);line(s,766,298,867,298,C.green,2,true);
txt(s,'c6 前驅時間上界 = 4 − 1 − 1 = 2；在 [1,1] 中取最大值 1。',95,433,1100,58,29,C.blue);
txt(s,'A→C：發送 1～2、接收 2～3；C→D：發送／接收 4～5。',95,536,1100,58,29,C.green);

s=base(21,'第二包：驗證後提交 c6、c7 與 C 曲線','只提交選定排程；c3、c4 的候選不占用全域資源。','目前 Commit 把 c6[1,2)、c7[4,5) 加入 F，並加入 C 的占用。c3 前綴與未選的 c4 都不提交。這裡仍沿用現行原型的中繼提交範圍，不把來源或目的地尚缺的功能畫成已完成。');
graph(s,{c6:C.green,c7:C.green},'C');chart(s,[{name:'第二包 C',points:C2,color:C.green},cap]);
txt(s,'F[c6]={[1,2)}；F[c7]={[4,5)}',105,535,1090,55,32,C.green);

s=base(22,'兩包完成：送達時間與資源預約','規劃第二包時已知第一包的未來預約，但仍可在較早時間抵達。','第一包先規劃，不等於第一包先抵達。它經 B 於 8 到 D；第二包經 C 於 5 到 D。中繼背景位在不同節點，各節點峰值最高 4。獨立核對器另外檢查來源與目的地，這個特殊案例沒有共用來源、沒有重疊的 D 接收，因此目前 Commit 缺口不改變結果；不可以外推到多包一般情況。');
graph(s,{c1:C.orange,c2:C.orange,c6:C.green,c7:C.green},'D');
table(s,[['Bundle','路徑','起送時間','整包到 D'],['第一包','X→B→D','2、6','8 秒'],['第二包','A→C→D','1、4','5 秒']],650,190,540,220,[105,160,145,130],25);
txt(s,'預約：c1[2,3)、c2[6,7)',650,455,540,38,26,C.orange);txt(s,'　　　c6[1,2)、c7[4,5)',650,510,540,38,26,C.green);

s=base(23,'第二包：Q 與拒絕原因總表','只有 c3→c5 因 Buffer 拒絕；c2 因預約、c8 因時間拒絕。','本表來自 walkthrough.json 的真實候選控制流程。Label 編號僅在第二包搜尋中有效。初始化先產生 c3、c4、c6，Q 以 key 排序。取出 c3 後試 c2、c5；取出 c6 後試 c7、c8；最後取出 c7 目的地。');
table(s,[['階段','處理','結果','Q 摘要：Label ID:key'],['初始化','c3、c4、c6','三個區間 Label','L1:2 → L3:3 → L2:8'],['取出 L1','c3→c2','唯一時段被預約','L3:3 → L2:8'],['同一個 L1','c3→c5','B 占用 8>4','L3:3 → L2:8'],['取出 L3','c6→c7','新增 L4，key=5','L4:5 → L2:8'],['同一個 L3','c6→c8','Head 3>Tail 2','L4:5 → L2:8'],['取出 L4','目的地 D','回溯 c6→c7','L2:8（不再展開）']],90,165,1100,410,[155,215,320,410],25);

s=base(24,'補充：c4 區間何時變成實際時間','固定 c4→c5 時，回溯會選 c4 的 s=8；這不是本例選中路徑。','這一頁解釋尚未展開的 c4 區間如何用，不把它冒充主搜尋實際發生的步驟。假設固定選 c4→c5，末跳 c5 的 s=10，前一跳上界 10−0−1=9；在 I=[7,8] 取最大值 8，故 B 於 9 收完，再等到 10 發送，D 於 12 收完。s=7 也是可行排程，但候選回溯採最晚前驅；這不表示它對後續 bundles 一定最好。');
graph(s,{c4:C.blue,c5:C.blue},'B');
txt(s,'c5 固定 s=10',650,175,550,48,34,C.blue);txt(s,'前驅上界：10−δ(c4)−d(c4)=9',650,242,550,60,29,C.ink);
txt(s,'在 I(c4)=[7,8] 內取最大值 → 8',650,328,550,60,30,C.green);txt(s,'c4：8 起送 → 9 到 B\nc5：10 起送 → 12 到 D',650,430,550,90,29,C.green);
txt(s,'主搜尋已在 key=5 的目的地結束；此頁只是區間回溯示例。',95,572,1100,44,26,C.gray);

s=base(25,'補充：預約如何切出可行起送區間','切的是起送時間集合；仍要完整保留每段連通區間。','獨立示例，非主案例的新預約。contact 開放 [1,10]，傳輸時間 1；原起送集合 [1,9]。若既有預約 [3,5)，相衝突的起送時間是 (3−1,5)=(2,5)，兩端 2、5 皆可緊貼使用，因此剩 [1,2] 與 [5,9]。之後還要做 Buffer 檢查，不能從剩餘總量夠就判整包可傳。');
timeline(s,[{label:'contact',bars:[[1,10,C.light]]},{label:'已預約 F',bars:[[3,5,C.orange]]},{label:'可行起送 I',bars:[[1,2,C.green],[5,9,C.green]]}],{x:300,y:200,w:850,min:0,max:10});
txt(s,'[1,9] − (2,5) = [1,2] ∪ [5,9]',180,500,970,64,39,C.green,'center');
txt(s,'一段預約可能把集合分成兩段；不是每個時間點各建 Label。',105,577,1090,43,28,C.ink);

s=base(26,'Label、Q 與 Reached 的分工','離開 Q 是取出來展開；被子 Label 引用的前驅仍須保留。','Q 是待展開 Label 的優先佇列，不是所有 Label 的儲存庫。ExtractMin 後取出的 Label 不再排隊，但已建立的子 Label 透過 pred 持有前驅物件，直到回溯不再需要它；不必因此新增研究狀態欄位或假裝程式已有全域 Labels／Processed 集合。Reached[c] 是以原始 contact 為索引的已達起送集合，不是 Label 清單。完整重複區間不重建，未涵蓋部分仍保留；不同 contacts 到同節點不能僅憑早到刪除。一般完備性與開閉端點仍待證。');
table(s,[['對象','用途'],['Q','只放待展開 Label；ExtractMin 後即離開 Q'],['pred 鏈','子 Label 引用前驅，供之後回溯；例如 L2.pred=L1'],['Reached[c]','記錄同 contact 已涵蓋的起送集合，避免重建'],['c3 → B 與 c4 → B','contact 不同；保留各自候選，不只看誰早到']],95,180,1090,280,[230,860],26);
txt(s,'New = C − Reached[c]',140,493,1000,55,37,C.blue,'center');
txt(s,'例：Reached[c4]=[7,8]，新候選也是 [7,8] → 不重建。',105,571,1090,42,27,C.gray);

s=base(27,'虛擬碼 1：逐包規劃與初始化','搜尋不預約資源；接受選定排程後才 Commit。','英文虛擬碼呈現最新候選流程。兩包依固定規劃順序，並非依最終抵達時間排序。SourceBufferFilter 在原型已實作。DestinationFilter 與來源／目的地 Commit 尚未實作，本簡報在相應頁面有明示。');
codes(s,['for each bundle B in planning order:','    goal ← SearchBundle(B)','    if goal is NONE: record NO_PATH; continue','    schedule ← Backtrack(goal)','    if not ValidateSchedule(schedule): save failure; STOP','    Commit(schedule)','', 'SearchBundle(B):','    Q ← empty priority queue; Reached ← empty','    for each contact c leaving source(B):','        C ← SourceBufferFilter(c, SourceRange(c))','        InsertLabels(c, C, SOURCE)'],90,158,1100,25,33);

s=base(28,'虛擬碼 2：取出與延伸 Label','收完整包才轉送；每次只展開目前接收節點的 outgoing contacts。','此頁區間搜尋原型沒有 RELAX、TRACK、Ch，也沒有逐秒迴圈。key 為 lo(I)+d+δ，pop 同 key 時以建立順序分辨。Reached 是在插入時移除已涵蓋時間，不是全域 node visited。沒有以資料證明一般最優性；此頁是目前控制流程。');
codes(s,['while Q is not empty:','    L1 = (c1, I1, pred1) ← ExtractMin(Q, key)','    if receiver(c1) = destination(B): return L1','    for each contact c2 leaving receiver(c1):','        C ← StartRange(c2, L1)','        C ← BufferFilter(C, L1, c2)','        InsertLabels(c2, C, L1)','return NONE','','InsertLabels(c, C, pred):','    New ← C − Reached[c]; Reached[c] ← Reached[c] ∪ New','    for each connected interval I in New: push (c,I,pred)'],90,158,1100,25,33);

s=base(29,'虛擬碼 3：StartRange 與 SourceRange','未提供 deadline 時，Tail 只使用 contact 結束時間限制。','延伸的 Head 為 max(a(c2),lo(I1)+δ1+d1)，這是 store-and-forward。Tail b−d 確保整包發送在 contact 結束前完成。可選 D* 需要再扣傳播延遲，確保整包抵達不逾期。程式目前的 P.T 是有限上界；此案例為 max(b+δ)=12，不構成額外 deadline。每個 F 預約排除的是開區間 (x−d,y)，允許剛好相接。');
codes(s,['StartRange(c2, L1):','    Head ← max(a(c2), lo(I1) + δ1 + d1)','    Tail ← b(c2) − d2','    if deadline D* is given: Tail ← min(Tail, D* − d2 − δ2)','    return RemoveBookings([Head,Tail], F[c2], d2)','','SourceRange(c):','    Head ← max(a(c), g); Tail ← b(c) − d(c)','    if deadline D* is given: Tail ← min(Tail, D* − d(c) − δ(c))','    return RemoveBookings([Head,Tail], F[c], d(c))','','RemoveBookings(C,F,d): remove (x−d,y) for every [x,y) in F'],90,155,1100,24,33);

s=base(30,'虛擬碼 4：BufferFilter','同時檢查接收、等待與發送；只接收可行還不夠。','固定下一跳起送 s2 時，前驅允許上界 U=s2−δ1−d1。候選只取 I1 中不超過 U 的最晚起送 s1*，以減少目前節點提前接收占用；此壓縮的充分性仍須正式證明。依背景曲線與分段邊界求可行 s2 區間，不枚舉所有實數。來源已實作的曲線檢查與尚未實作的目的地檢查分開說明。');
codes(s,['U(s2) ← s2 − δ1 − d1','s1* ← latest reachable start in I1 not later than U(s2)','Occ(t,s2) ← O_n(t) + Received(t,s1*) − Sent(t,s2)','', 'BufferFilter(C,L1,c2):','    split C at changes of s1* and occupancy expressions','    solve Occ(t,s2) ≤ M_n throughout each node visit','    return all feasible connected start intervals'],90,165,1100,26,39);
txt(s,'SourceBufferFilter：從 g 持有整包，傳送時逐 byte 釋放。',95,527,1090,42,27,C.green);
txt(s,'DestinationFilter：接收期間檢查，交付後釋放（原型尚未實作）。',95,578,1090,42,27,C.red);

s=base(31,'虛擬碼 5：回溯、驗證與提交','前驅最晚取值是目前選擇規則，不保證對後續 bundles 最好。','回溯從目的地 Label 的區間下界起送，逐步求前驅最大可用起送時間。ValidateSchedule 應檢查完整排程與全程 Buffer；原型現有 replay 未檢查目的地。Commit 實際只寫 F 及中繼 O；來源與目的地需補完。這頁不新增未經同意的 RetimePath、incompleteLB 或保護 ε。');
txt(s,'Backtrack(goal)',95,168,530,40,31,C.blue);codes(s,['L ← goal; s ← lo(I(L))','schedule ← [(c(L),s)]','while pred(L) ≠ SOURCE:','    P ← pred(L); U ← s − d(c(P)) − δ(c(P))','    s ← max {x in I(P) : x ≤ U}','    prepend (c(P),s); L ← P','return schedule'],95,225,535,21,34);
txt(s,'Validate → Commit',680,168,500,40,31,C.blue);codes(s,['check connectivity and s2 ≥ A1','check contact windows and F','check Buffer throughout visits','if valid:','    add [s,s+d) to F[c]','    add transit occupancy to O'],680,225,515,23,37);
txt(s,'待補：目的地檢查，以及來源／目的地的完整占用提交。',95,555,1090,54,30,C.red);

s=base(32,'目前驗證範圍與下一步','本例已重算核對；一般正確性與完整多包實驗尚未完成。','此簡報本例兩包由現行 store_label.py 求得，逐步鏡像流程與原型結果一致，另用四分之一秒小例窮舉及不共用 ramp/occ/filter 的完整來源、中繼、目的地重放核對。這不是新的研究級實驗或一般證明。GitHub 文件記錄的 3000 例是既有結果，本次未重跑。沒有執行 Alhajj/Corlay baseline；舊網頁與本版方法尚不一致。');
bullets(s,['本例核對：X→B→D 在 8 秒；A→C→D 在 5 秒','既有紀錄：3,000 個小例與格點窮舉一致，非一般證明','待補：目的地檢查、來源／目的地 Commit、開閉端點','再完成：正式證明、完整實驗矩陣與原論文 baseline'],95,180,1090,31,90);
txt(s,'候選實作：src/experiments/store_forward/store_label.py',95,575,1090,42,25,C.gray);

await fs.writeFile(path.join(BUILD,'slide_notes.json'),JSON.stringify(notes,null,2));
await fs.writeFile(path.join(BUILD,'draft.pptx').replace(/\.pptx$/,'.inspection.ndjson'),(await p.inspect({kind:'slide,textbox,table,chart',maxChars:500000})).ndjson);
await (await PresentationFile.exportPptx(p)).save(path.join(BUILD,'draft.pptx'));
console.log('EXPORTED',p.slides.items.length);
for(let i=0;i<p.slides.items.length;i++) {
 const img=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,'final-preview',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await img.arrayBuffer()));
 console.log('RENDER',i+1);
}
