# 程式導讀圖：只描述既有架構與控制流程，不執行搜尋或產生研究結果。
"""Render editable SVG and PNG guides for the modular PPT implementation."""
from pathlib import Path
import sys

# 優先使用目前 Python；若繪圖依賴放在既有暫存資料夾，才加入該位置。
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tmp' / 'validation_plot_dependencies'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, Rectangle, Polygon

FONT = FontProperties(fname='C:/Windows/Fonts/kaiu.ttf', size=14)
OUT = ROOT / 'output/figures/code_guides_20261012'


# 建立一張獨立圖；圖元用資料座標定位，保留空間給分支標籤。
def canvas(width, height, title):
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    ax.set(xlim=(0, width), ylim=(0, height))
    ax.axis('off')
    ax.text(width/2, height-.38, title, ha='center', va='top',
            fontproperties=FONT.copy(), fontsize=22, color='#253b70')
    fig.subplots_adjust(left=.015, right=.985, bottom=.01, top=.99)
    return fig, ax


# 方框表示處理步驟，菱形表示判斷；SVG 文字保留為可編輯文字。
def box(ax, x, y, text, width=3.6, height=1.15, decision=False, tint=False):
    color = '#eaf2fb' if tint else '#ffffff'
    if decision:
        patch = Polygon([(x-width/2,y),(x,y+height/2),(x+width/2,y),(x,y-height/2)],
                        closed=True, facecolor=color, edgecolor='#304d7d', lw=1.4)
    else:
        patch = Rectangle((x-width/2,y-height/2),width,height,
                          facecolor=color,edgecolor='#304d7d',lw=1.4)
    ax.add_patch(patch)
    ax.text(x,y,text,ha='center',va='center',fontproperties=FONT,linespacing=1.35)


# 折線中間段不帶箭頭，只有最後一段帶箭頭，避免誤認中途已到終點。
def arrow(ax, points, label=None, label_at=None):
    for a,b in zip(points[:-2],points[1:-1]):
        ax.plot([a[0],b[0]],[a[1],b[1]],color='#596777',lw=1.3)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',
                                mutation_scale=13,lw=1.3,color='#596777'))
    if label:
        x,y=label_at or points[len(points)//2]
        ax.text(x,y,label,ha='center',va='center',fontproperties=FONT,fontsize=12,
                bbox=dict(facecolor='white',edgecolor='none',pad=1))


# 同一張圖保存兩種格式；不更新任何既有實驗資料。
def save(fig, name):
    OUT.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUT/(name+'.png'),facecolor='white')
    with matplotlib.rc_context({'svg.fonttype':'none'}):
        fig.savefig(OUT/(name+'.svg'),facecolor='white')
    path=OUT/(name+'.svg')
    path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf8').splitlines())+'\n',
                    encoding='utf8',newline='\n')
    plt.close(fig)


# 輸入、方法與執行器分開；共享檢查器及預約狀態不塞進演算法 plug-in。
def architecture():
    fig,ax=canvas(14,12.6,'系統架構：拓樸、需求、演算法可替換')
    for x,text in [(2.3,'experiment.json\n演算法／Δ／T'),(7,'topology.json + CSV\n節點／Buffer／Contacts'),(11.7,'bundles.json\n需求／規劃順序')]:
        box(ax,x,10.9,text,width=4.1)
        arrow(ax,[(x,10.3),(x,9.6),(7,9.6),(7,9.15)])
    box(ax,7,8.55,'config.py\n載入、組合、驗證輸入',width=4.1,tint=True)
    arrow(ax,[(7,7.97),(7,7.05)])
    box(ax,7,6.45,'runner.py\n每次處理一個 Bundle',width=4.1,tint=True)
    box(ax,2.3,6.45,'algorithms.py\n選擇單包搜尋函式',width=4.1)
    arrow(ax,[(4.35,6.45),(4.95,6.45)],'提供函式',(4.65,6.8))
    box(ax,2.3,4.15,'proposed_v04.py\nLabel Setting 搜尋',width=4.1)
    arrow(ax,[(5.1,5.87),(5.1,4.15),(4.35,4.15)],'呼叫',(5.45,5))
    arrow(ax,[(2.3,4.73),(2.3,5.35),(4.7,5.35),(4.7,6.05),(4.95,6.05)],
          '回傳候選路徑',(3.5,5.6))
    box(ax,11.7,6.45,'獨立完整路徑檢查\n小案例可選完整搜尋比對',width=4.1)
    arrow(ax,[(9.05,6.45),(9.65,6.45)])
    box(ax,7,3.05,'R：剩餘 Contact 容量\nO：既有 Buffer 預約',width=4.1,tint=True)
    arrow(ax,[(11.7,5.87),(11.7,4.95),(7,4.95),(7,3.63)],'驗證通過才更新',(9.5,5.15))
    arrow(ax,[(7,3.63),(7,5.87)],'下一包使用新狀態',(8.4,4.15))
    box(ax,11.7,1.05,'CSV／JSON／報告\nGUI／網頁重播',width=4.1)
    arrow(ax,[(9.05,3.05),(11.7,3.05),(11.7,1.63)])
    ax.text(2.3,1.6,'搜尋期間不修改 R、O\n顯示端不重新決定路徑\n目前未檢查鏈路時段互斥',ha='center',va='center',fontproperties=FONT)
    save(fig,'system_architecture')


# 外層逐包流程：無解不預約；驗證差異必須保存並停止，不能直接改答案。
def sequential():
    fig,ax=canvas(12,16,'逐包規劃與資源預約流程')
    box(ax,6,14.6,'載入並驗證設定\n建立初始 R、O')
    box(ax,6,12.8,'還有下一個 Bundle？',decision=True,height=1.3,width=4.3)
    arrow(ax,[(6,14.02),(6,13.45)])
    box(ax,10,12.8,'輸出結果\n結束',width=2.6)
    arrow(ax,[(8.15,12.8),(8.7,12.8)],'否',(8.45,13.12))
    box(ax,6,10.8,'單包搜尋（R、O 固定）\n可選：完整搜尋核對答案')
    arrow(ax,[(6,12.15),(6,11.38)],'是',(6.35,11.8))
    box(ax,6,8.8,'找到完整路徑？',decision=True,height=1.3,width=4.3)
    arrow(ax,[(6,10.22),(6,9.45)])
    box(ax,2,8.8,'記錄格點上無路徑\n不更新 R、O',width=3.3)
    arrow(ax,[(3.85,8.8),(3.65,8.8)],'否',(3.75,9.18))
    arrow(ax,[(2,9.38),(2,12.8),(3.85,12.8)])
    box(ax,6,6.8,'獨立檢查完整排程\n核對資源更新')
    arrow(ax,[(6,8.15),(6,7.38)],'是',(6.35,7.8))
    box(ax,6,4.8,'檢查一致？',decision=True,height=1.3,width=4.3)
    arrow(ax,[(6,6.22),(6,5.45)])
    box(ax,10,4.8,'保存失敗案例\n立即停止',width=2.6)
    arrow(ax,[(8.15,4.8),(8.7,4.8)],'否',(8.45,5.12))
    arrow(ax,[(7.8,10.8),(11.7,10.8),(11.7,4.8),(11.3,4.8)],
          '答案比對不一致',(9.6,11.15))
    box(ax,6,2.8,'扣除選定路徑容量\n加入完整 Buffer 預約',tint=True)
    arrow(ax,[(6,4.15),(6,3.38)],'是',(6.35,3.8))
    arrow(ax,[(4.2,2.8),(.15,2.8),(.15,12.8),(3.85,12.8)])
    ax.text(6,.9,'資源在規劃時預約；占用對應到未來的各傳送時段。\n逾時必須另外記錄，不能當作「無路徑」。',ha='center',fontproperties=FONT)
    save(fig,'sequential_reservation_flow')


# 內層三重結構：Q → outgoing Contact → 起送時間；失敗要回到正確迴圈層。
def label_setting():
    fig,ax=canvas(14,23,'單包 Label Setting：保留起送時間枚舉')
    box(ax,6.6,21.6,'來源 Buffer 檢查\n通過後建立 L0 與 Q')
    box(ax,11.7,21.6,'來源超限\n回傳無路徑',width=3.1)
    arrow(ax,[(8.4,21.6),(10.15,21.6)],'不通過',(9.3,21.95))
    box(ax,6.6,19.8,'Q 非空？',decision=True,height=1.3,width=3.9)
    arrow(ax,[(6.6,21.02),(6.6,20.45)])
    box(ax,11.7,19.8,'NO_ROUTE_ON_GRID',width=3.1)
    arrow(ax,[(8.55,19.8),(10.15,19.8)],'否',(9.3,20.15))
    box(ax,6.6,18,'取出抵達時間最早的 Label\n已失效者跳過')
    arrow(ax,[(6.6,19.15),(6.6,18.58)],'是',(6.95,18.85))
    arrow(ax,[(4.8,18),(1.2,18),(1.2,19.8),(4.65,19.8)],'失效',(2.6,18.3))
    box(ax,6.6,16.2,'目前節點是目的地？',decision=True,height=1.3,width=4.5)
    arrow(ax,[(6.6,17.42),(6.6,16.85)])
    box(ax,11.7,16.2,'沿 pred 回溯\n回傳路徑與起送時間',width=3.4)
    arrow(ax,[(8.85,16.2),(10,16.2)],'是',(9.4,16.55))
    box(ax,6.6,14.2,'還有 outgoing Contact？',decision=True,height=1.3,width=4.5)
    arrow(ax,[(6.6,15.55),(6.6,14.85)],'否',(6.95,15.2))
    arrow(ax,[(4.35,14.2),(.6,14.2),(.6,19.8),(4.65,19.8)],'否：回到 Q',(2.3,14.55))
    box(ax,6.6,12.2,'容量足夠且有候選時間？',decision=True,height=1.4,width=4.7)
    arrow(ax,[(6.6,13.55),(6.6,12.9)],'是：選 c',(7.3,13.2))
    arrow(ax,[(4.25,12.2),(2.1,12.2),(2.1,14.2),(4.35,14.2)],'否：下一 Contact',(2.7,12.55))
    box(ax,6.6,10.2,'還有未試的起送時間 s？',decision=True,height=1.4,width=4.7)
    arrow(ax,[(6.6,11.5),(6.6,10.9)],'是',(6.95,11.2))
    arrow(ax,[(4.25,10.2),(1.5,10.2),(1.5,14.2),(4.35,14.2)],'否：下一 Contact',(2.6,10.55))
    box(ax,6.6,8.3,'取下一個 s，計算完整抵達時間\n檢查時窗、T、傳送端與接收端 Buffer',width=5.3,height=1.2)
    arrow(ax,[(6.6,9.5),(6.6,8.9)],'是',(6.95,9.2))
    box(ax,6.6,6.3,'這次延伸可行？',decision=True,height=1.3,width=4.3)
    arrow(ax,[(6.6,7.7),(6.6,6.95)])
    box(ax,11.7,6.3,'繼續下一個 s\n保留同一 Contact',width=3.3,tint=True)
    arrow(ax,[(8.75,6.3),(10.05,6.3)],'否',(9.4,6.65))
    arrow(ax,[(11.7,6.88),(11.7,10.2),(8.95,10.2)])
    box(ax,6.6,4.3,'建立候選 Label N\n與有效同節點 Label 做 dominance',width=5.3,height=1.2)
    arrow(ax,[(6.6,5.65),(6.6,4.9)],'是',(6.95,5.2))
    box(ax,6.6,2.3,'N 被支配：丟棄 N\n否則：標記舊受支配者，將 N 加入 Q\n保留被引用的前驅紀錄',width=5.5,height=1.5)
    arrow(ax,[(6.6,3.7),(6.6,3.05)])
    arrow(ax,[(9.35,2.3),(11.7,2.3),(11.7,5.72)])
    ax.text(6.6,.65,'所有候選僅是規劃方案，搜尋中不扣全域容量、不提交 Buffer。\n先檢查延伸，再做 dominance，最後才加入 Q。',ha='center',fontproperties=FONT)
    save(fig,'label_setting_flow')


# 明確入口，匯入模組不會自動產生圖片或觸發路由。
if __name__ == '__main__':
    architecture()
    sequential()
    label_setting()
    print(OUT)
