# 由驗證資料繪製既有圖解；圖像是說明，不取代數值核對。
"""Nine reproducible scientific walkthrough diagrams, fixed topology throughout."""
from pathlib import Path
import sys
import json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp'/'validation_plot_dependencies'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
from matplotlib.font_manager import FontProperties, fontManager
import numpy as np
from PIL import Image, ImageOps, ImageDraw

FONT=Path('C:/Windows/Fonts/kaiu.ttf')
if not FONT.exists():
    raise FileNotFoundError('Required font missing: 標楷體 (kaiu.ttf)')
fontManager.addfont(str(FONT))
plt.rcParams['font.family']=[FontProperties(fname=str(FONT)).get_name(),'DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False
POS={'X':(0,2.6),'A':(0,0.4),'B':(2.8,2.0),'C':(2.8,-0.3),'D':(5.6,1.2)}
BLUE='#2563A6';ORANGE='#C16B17';GREEN='#16794D';RED='#B6343A';GRAY='#A8B0BC';INK='#172B45'


# 讀取既有 trace 與數值，輸出各步驟圖解；不執行效能實驗。
def run():
    data=json.loads((ROOT/'output/validation/walkthrough_trace.json').read_text(encoding='utf-8'))
    edges=data['case']['contacts']
    out=ROOT/'figures'/'algorithm_walkthrough';out.mkdir(parents=True,exist_ok=True)
    plans=[
      ('step_00_topology','固定驗證拓樸',None,[],[],[],[
       'Bundle 1：X → D，g=0，S=4 MB','Bundle 2：A → D，g=1，S=4 MB','依序規劃；每個節點 M=4 MB','Δ=1 秒，T=12 秒','c4 可從第 7 或 8 秒開始傳送'],0),
      ('step_01_source_label','Bundle 1：建立來源 label','X',[],[],[],[
       'L0 = (X, 0, U=0)','Q = [L0]','只延伸 X 的 outgoing contact c1','等待 0–2，發送 2–3','搜尋尚未提交任何預約'],0),
      ('step_02_first_extension','Bundle 1：c1 延伸成功','B',['c1'],[],[],[
       'L1 = (B, 3, {c1:4})','s=2，f=3，δ=0，arrival=3','Temporal：2+1 ≤ 3 ✓','Quota：0+4 ≤ 4 ✓','兩端 buffer 峰值皆為 4 MB'],1),
      ('step_03_feasibility_check','Bundle 1：檢查兩個後續 contacts','B',[],['c2','c5'],[],[
       'L1 經 c2：s=6，f=7，arrival=8','L1 經 c5：s=10，f=11，arrival=12','兩者 quota / window / buffer 均通過','L2=(D,8)，L3=(D,12)','Q = [L2, L3]；尚未提交'],2),
      ('step_04_dominance','Bundle 1：先檢查 dominance', 'D',[],['c2','c5'],[],[
       'L2: D@8，U={c1:4,c2:4}','L3: D@12，U={c1:4,c5:4}','U_L2[c2]=4 > U_L3[c2]=0','因此目前規則不能刪 L3','下一步取出 D@8，才終止搜尋','真正的 pruning 見 step 07'],2),
      ('step_05_bundle1_route','Bundle 1：選定 c1 → c2','D',['c1','c2'],[],[],[
       '有效目的地 L2 從 Q 取出','X 發送 2–3；B 完整接收於 3','B 等待 3–6；發送 6–7','D 接收 7–8；完整 arrival=8','確認整條 route 後才能提交'],2),
      ('step_06_resource_update','提交 Bundle 1：更新 quota 與 buffer',None,['c1','c2'],[],[],[
       'c1 quota：4 → 0','c2 quota：4 → 0','未選 c5：仍為 4','B：2–3 接收、3–6 等待、6–7 釋放','下一包讀取這份預約，不 reset'],3),
      ('step_07_bundle2_search','Bundle 2：失敗分支與實際 pruning','B',['c4','c5'],[],['c2','c7','c8'],[
       'B@2 → c5：等待會超量，拒絕','C@3 → c7：quota 2 < 4，拒絕','C@3 → c8：已無完整傳輸時間','L2=B@8 與 L3=B@9：同 U={c4:4}','8–9 可等待：L2 取代 L3（刪除）','保留 B@8 → c5 → D@12'],4),
      ('step_08_final_state','最終狀態：兩包均完成','D',['c1','c2','c4','c5'],[],[],[
       'Bundle 1：c1 → c2，arrival=8','Bundle 2：c4 → c5，arrival=12','c1=0，c2=0，c4=4，c5=0','B 的總占用峰值=4 MB','前包預約已改變後包所選路徑','本圖為格點／aggregate model'],5),
    ]
    radii={'c1':0,'c2':-.20,'c3':-.13,'c4':.13,'c5':.20,'c6':0,'c7':-.15,'c8':.15}
    # Label locations are fixed across all frames, just like the nodes and arcs.
    lp={'c1':(1.35,2.80),'c2':(4.28,2.14),'c5':(4.25,1.12),
        'c3':(1.25,1.58),'c4':(1.47,.79),'c6':(1.27,-.24),
        'c7':(4.10,.53),'c8':(4.42,-.14)}
    files=[]
    for index,(name,title,active,selected,candidates,rejected,notes,mode) in enumerate(plans):
        fig=plt.figure(figsize=(16,9),facecolor='white')
        fig.text(.045,.94,f'{index:02d}  {title}',fontsize=24,weight='bold',color=INK)
        fig.text(.045,.893,'所有 contacts：rate=4 MB/s；標籤顯示 window、quota q、propagation δ。傳完後才轉送。',fontsize=12,color='#526174')
        ax=fig.add_axes([.04,.34,.60,.50]);ax.set_xlim(-.55,6.2);ax.set_ylim(-.8,3.2);ax.axis('off')
        for c in edges:
            cid=c['id'];q=c['quota']
            if mode>=3 and cid in ('c1','c2'):q='0'
            if mode==5 and cid=='c4':q='4'
            if mode==5 and cid=='c5':q='0'
            col=GREEN if cid in selected else ORANGE if cid in candidates else RED if cid in rejected else GRAY
            u,v=POS[c['u']],POS[c['v']]
            ax.add_patch(FancyArrowPatch(u,v,connectionstyle=f'arc3,rad={radii[cid]}',arrowstyle='-|>',
                                        mutation_scale=17,linewidth=2.6 if cid in selected+candidates+rejected else 1.4,
                                        color=col,shrinkA=20,shrinkB=20,linestyle='--' if cid in rejected else '-'))
            tx,ty=lp[cid]
            ax.text(tx,ty,f"{cid} [{c['start']},{c['end']})\nq={q}, δ={c['delay']}",ha='center',va='center',fontsize=10.5,
                    color=col if col!=GRAY else '#586677',bbox=dict(boxstyle='round,pad=.25',fc='white',ec='none',alpha=.94))
        for node,(x,y) in POS.items():
            ax.add_patch(Circle((x,y),.20,facecolor=BLUE if node==active else '#EDF2F7',edgecolor=BLUE if node==active else INK,linewidth=2))
            ax.text(x,y,node,ha='center',va='center',fontsize=16,weight='bold',color='white' if node==active else INK)
        box=fig.add_axes([.665,.33,.305,.52]);box.axis('off')
        box.text(0,1,'本步 label / 判定',fontsize=17,weight='bold',va='top',color=INK)
        for n,note in enumerate(notes):
            box.text(0,.87-n*.125,'• '+note,fontsize=12.5,va='top',color=RED if ('拒絕' in note or '刪除' in note) else INK)
        fig.text(.055,.305,'藍色節點：active　綠色：選定／通過　橘色：候選　紅色虛線：拒絕　灰色：其他 contact',fontsize=11,color='#526174')
        bx=fig.add_axes([.09,.09,.82,.15])
        t=np.linspace(0,12,481)
        first=np.minimum(4,np.maximum(0,4*(t-2)))-np.minimum(4,np.maximum(0,4*(t-6)))
        second=np.minimum(4,np.maximum(0,4*(t-7)))-np.minimum(4,np.maximum(0,4*(t-10)))
        early=np.minimum(4,np.maximum(0,4*(t-1)))-np.minimum(4,np.maximum(0,4*(t-10)))
        bx.axhline(4,color=INK,lw=1.2,ls=':',label='B 上限 4 MB')
        if mode==0:bx.plot(t,t*0,color=GRAY,label='尚無 B 預約')
        if mode==1:bx.plot([2,3],[0,4],color=ORANGE,lw=2.5,label='本次接收（未提交）')
        if mode==2:bx.plot(t,first,color=ORANGE,lw=2.5,ls='--',label='c1→c2 候選排程（未提交）')
        if mode>=3:bx.plot(t,first,color=BLUE,lw=2.5,label='Bundle 1 已提交占用')
        if mode==4:
            bx.plot(t,first+early,color=RED,lw=1.8,ls='--',label='早到分支若等至 10：超量')
            bx.plot(t,first+second,color=ORANGE,lw=2,label='晚到分支＋既有占用')
        if mode==5:
            bx.plot(t,second,color=ORANGE,lw=2.5,label='Bundle 2 已提交占用')
            bx.plot(t,first+second,color=INK,lw=1,ls='--',label='總占用')
        bx.set_xlim(0,12);bx.set_ylim(-.2,8.7 if mode==4 else 5.2)
        bx.set_xticks(range(13));bx.set_ylabel('B buffer (MB)',fontsize=10);bx.set_xlabel('Time (s)',fontsize=10)
        bx.grid(alpha=.16);bx.legend(loc='upper right',fontsize=8.5,ncol=2)
        fig.text(.045,.015,'資料來源：walkthrough_trace.json；原始 v04 未修改。圖序是解說順序，完整每次 POP/EXTEND 見 walkthrough 文件。',fontsize=9,color='#526174')
        path=out/(name+'.png');fig.savefig(path,dpi=160,facecolor='white');plt.close(fig);files.append(path)
    thumbs=[]
    for path in files:
        with Image.open(path) as im:
            thumbs.append(ImageOps.contain(im.convert('RGB'),(640,360)))
    sheet=Image.new('RGB',(1920,1080),'white')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%3)*640,(i//3)*360))
    sheet.save(out/'walkthrough_contact_sheet.png')
    (out/'README.md').write_text('# Walkthrough figures\n\n九張 PNG 為 2560×1440（16:9），使用固定拓樸與固定 contact 位置。文字使用標楷體（DFKai-SB / kaiu.ttf），缺少的特殊符號以 DejaVu Sans 補足。'+
        '\n\n'+ '\n'.join('- '+p.name for p in files)+
        '\n\nstep_04 的 Bundle 1 不觸發 pruning；step_07 才顯示 Bundle 2 的實際 pruning。紅色 c5 等待失敗屬 B@2 label 的延伸，不代表整個 c5 不可用。'+
        '\n\n使用 `python -m src.validation.render_figures` 重建。matplotlib 安裝於專案 tmp/validation_plot_dependencies，未更改系統 Python。',encoding='utf-8')
    print('Generated',len(files),'figures and contact sheet at',out)

if __name__=='__main__':run()
