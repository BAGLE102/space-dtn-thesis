"""Tkinter desktop viewer and launcher for the existing frozen v04 router."""
import argparse
import json
import math
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .process_view import load_run, load_suite

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = ROOT/'output/experiments/small_suite_v01_20261011'


def enable_dpi_awareness():
    """Keep Tk window coordinates consistent with Windows display scaling."""
    if os.name == 'nt':
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def number(value):
    return float(Fraction(str(value)))


def curve_value(curve, time):
    values = []
    for lo, hi, y0, y1 in curve:
        lo, hi, y0, y1 = map(number, (lo, hi, y0, y1))
        if lo <= time <= hi:
            values.append(y0 if hi == lo else y0+(y1-y0)*(time-lo)/(hi-lo))
    return max(values, default=0)


def event_text(run, record, event):
    """Explain the logged result, without inventing a new feasibility rule."""
    kind = event['event']
    if kind == 'INIT':
        b = record['bundle']
        return '建立 L0 並加入 Q', f"{b['source']} → {b['dest']}；生成 {b['g']} 秒；大小 {b['size']} MB。"
    if kind == 'POP':
        return f"取出 {event['selected']}，嘗試下一跳", '此時仍在搜尋；尚未接受完整路徑。'
    if kind == 'EXTEND':
        if event['reason'] != 'PASS':
            title = f"{event['contact']}：{'Buffer 超限' if event['reason']=='BUFFER' else '時間或容量不符'}，不建立可保留的 Label"
        elif event.get('dominated_by'):
            title = f"{event['new_label']} 被 {', '.join(event['dominated_by'])} 支配，不加入 Q"
        else:
            title = f"{event['contact']} 通過，建立 {event['new_label']} 並加入 Q"
        detail = f"發送 {event['s']}–{event['f']} 秒；接收 {event['h']}–{event['arrival']} 秒。"
        if 'sender_peak' in event:
            edge = next(c for c in run['contacts'] if c['id'] == event['contact'])
            detail += (f" {edge['u']} 峰值 {event['sender_peak']}/{run['buffers'][edge['u']]} MB"
                       f"（第 {event['sender_peak_time']} 秒）；{edge['v']} 峰值 "
                       f"{event['receiver_peak']}/{run['buffers'][edge['v']]} MB。")
        if event.get('removed'):
            detail += f" 標記 {', '.join(event['removed'])} 遭支配；保留前驅紀錄。"
        return title, detail
    if kind == 'CONTACT_QUOTA_FAIL':
        return f"{event['contact']}：容量不足", f"已用 {event['used']} + 本包 {record['bundle']['size']} > 剩餘 {event['quota']} MB；未進行後續 Buffer 檢查。"
    if kind == 'CONTACT_TIME_FAIL':
        return f"{event['contact']}：時窗不足", f"最早起送 {event['earliest']} 秒；最晚須於 {event['latest']} 秒起送。"
    if kind == 'GOAL':
        return f"取出目的地 Label {event['selected']}，完整抵達 {record['arrival']} 秒", '沿 pred 回溯：'+' → '.join(c for c, _ in record['hops'])+'；完整驗證後才更新資源。'
    if kind == 'SOURCE_FAIL':
        return '來源 Buffer 無法容納整包', '既有程式的初始化檢查未通過；此包不預約資源。'
    if kind == 'STALE':
        return f"跳過遭支配的 {event['selected']}", '佇列暫留的失效項目不再延伸。'
    return 'Q 已耗盡，格點上無路徑', '此包不扣除容量或提交 Buffer 預約。'


class ExperimentGUI:
    def __init__(self, root, suite=None):
        self.root = root
        self.data, self.ci, self.bi, self.step, self.time = [], 0, 1, 0, 0.0
        self.timer = self.process = self.poll_timer = self.log = None
        self.updating = False
        root.title('Space DTN 實驗與 Label Setting 過程')
        width, height = min(1180, root.winfo_screenwidth()-60), min(850, root.winfo_screenheight()-100)
        root.geometry(f'{width}x{height}+25+25')
        root.minsize(min(900, width), min(780, height))
        root.option_add('*Font', ('標楷體', 12))
        style = ttk.Style(root)
        style.configure('Treeview', font=('標楷體', 11), rowheight=28)
        style.configure('Treeview.Heading', font=('標楷體', 11))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main = ttk.Frame(root, padding=12)
        main.grid(sticky='nsew')
        main.columnconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)
        toolbar = ttk.Frame(main)
        toolbar.grid(row=0, sticky='ew')
        ttk.Button(toolbar, text='開啟實驗結果', command=self.open_results).pack(side='left')
        ttk.Button(toolbar, text='選擇 JSON 案例', command=self.choose_config).pack(side='left', padx=6)
        self.config = tk.StringVar(value=str(ROOT/'configs/walkthrough.json'))
        ttk.Entry(toolbar, textvariable=self.config, width=40).pack(side='left', fill='x', expand=True)
        actions = ttk.Frame(main)
        actions.grid(row=1, sticky='ew', pady=5)
        self.oracle = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions, text='完整搜尋核對（小案例）', variable=self.oracle).pack(side='left', padx=6)
        self.run_button = ttk.Button(actions, text='執行案例', command=self.start_run)
        self.run_button.pack(side='left')
        self.cancel_button = ttk.Button(actions, text='停止執行', command=self.cancel_run, state='disabled')
        self.cancel_button.pack(side='left', padx=6)
        ttk.Label(actions, text='v04 · 保留枚舉／usage cache · 非 SimPy', wraplength=380).pack(side='left', padx=12)
        choices = ttk.Frame(main)
        choices.grid(row=2, sticky='ew')
        choices.columnconfigure(1, weight=2)
        choices.columnconfigure(3, weight=1)
        ttk.Label(choices, text='案例').grid(row=0, column=0)
        self.case_box = ttk.Combobox(choices, state='readonly', width=40)
        self.case_box.grid(row=0, column=1, sticky='ew', padx=6)
        self.case_box.bind('<<ComboboxSelected>>', self.change_case)
        self.mode_box = ttk.Combobox(choices, state='readonly', values=['搜尋步驟', '已接受排程'], width=13)
        self.mode_box.current(0)
        self.mode_box.grid(row=0, column=2, padx=6)
        self.mode_box.bind('<<ComboboxSelected>>', self.change_mode)
        self.bundle_box = ttk.Combobox(choices, state='readonly', width=25)
        self.bundle_box.grid(row=0, column=3, sticky='ew', padx=6)
        self.bundle_box.bind('<<ComboboxSelected>>', self.change_bundle)
        controls = ttk.Frame(main)
        controls.grid(row=3, sticky='ew', pady=8)
        ttk.Button(controls, text='上一步', command=lambda:self.move(-1)).pack(side='left')
        self.play_button = ttk.Button(controls, text='播放', command=self.play)
        self.play_button.pack(side='left', padx=6)
        ttk.Button(controls, text='下一步', command=lambda:self.move(1)).pack(side='left')
        self.position = tk.StringVar()
        ttk.Label(controls, textvariable=self.position, width=22).pack(side='left', padx=8)
        self.scale = tk.Scale(controls, from_=0, to=1, orient='horizontal', showvalue=False,
                              command=self.seek, resolution=1, highlightthickness=0)
        self.scale.pack(side='left', fill='x', expand=True)
        self.status = tk.StringVar()
        self.detail = tk.StringVar()
        self.status_label = ttk.Label(main, textvariable=self.status, wraplength=1080)
        self.status_label.grid(row=4, sticky='w', pady=4)
        self.detail_label = ttk.Label(main, textvariable=self.detail, wraplength=1080)
        self.detail_label.grid(row=5, sticky='w', pady=(0, 6))
        panes = ttk.Panedwindow(main, orient='horizontal')
        panes.grid(row=6, sticky='nsew')
        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=3)
        panes.add(right, weight=2)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        self.graph = tk.Canvas(left, background='#ffffff', highlightthickness=0, height=330)
        self.graph.grid(sticky='nsew')
        self.graph.bind('<Configure>', lambda event:self.draw_graph())
        self.contact_heading = tk.StringVar()
        ttk.Label(left, textvariable=self.contact_heading).grid(row=1, sticky='w', pady=5)
        self.contacts = self.tree(left, ('Contact', '方向', '時窗', '速率', '延遲', '剩餘容量'), 2, height=5)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        self.queue_text = tk.StringVar()
        ttk.Label(right, textvariable=self.queue_text, wraplength=430).grid(row=0, sticky='w', pady=5)
        self.queue = self.tree(right, ('Label', '節點', 'Contact', '抵達', '起送', 'pred'), 1, height=5)
        self.buffer_canvas = tk.Canvas(right, background='#ffffff', highlightthickness=0, height=220)
        self.buffer_canvas.grid(row=2, sticky='nsew', pady=8)
        self.buffer_canvas.bind('<Configure>', lambda event:self.draw_buffers())
        buffer_scroll = ttk.Scrollbar(right, orient='vertical', command=self.buffer_canvas.yview)
        buffer_scroll.grid(row=2, column=1, sticky='ns')
        self.buffer_canvas.configure(yscrollcommand=buffer_scroll.set)
        self.bundle_status = tk.StringVar()
        ttk.Label(right, textvariable=self.bundle_status, wraplength=430).grid(row=3, sticky='w')
        self.footer = tk.StringVar(value='等待載入結果。')
        ttk.Label(main, textvariable=self.footer, wraplength=1080).grid(row=7, sticky='w', pady=(8, 0))
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<Configure>', self.resize_labels)
        if suite and Path(suite).exists():
            self.load_results(suite)

    def tree(self, parent, columns, row, height):
        frame = ttk.Frame(parent)
        frame.grid(row=row, sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=height)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=75, minwidth=55, anchor='center')
        tree.grid(sticky='nsew')
        bar = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        bar.grid(row=1, sticky='ew')
        vertical = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        tree.configure(xscrollcommand=bar.set, yscrollcommand=vertical.set)
        return tree

    def resize_labels(self, event):
        if event.widget == self.root:
            for label in (self.status_label, self.detail_label):
                label.configure(wraplength=max(650, event.width-40))

    @property
    def run(self):
        return self.data[self.ci]

    @property
    def record(self):
        return self.run['records'][self.bi]

    @property
    def searching(self):
        return self.mode_box.current() == 0

    def events(self):
        initial = [dict(event='INIT', queue_before=[], queue_after=['L0'])] if 'L0' in self.record['labels'] else []
        return initial+self.record['trace']

    def load_results(self, path):
        path = Path(path)
        if (path/'manifest.json').exists():
            data = load_suite(path)
            # The browser loader omits paths; restore them for desktop use.
            manifest = json.loads((path/'manifest.json').read_text(encoding='utf8'))
            for run, entry in zip(data, manifest['cases']):
                run['folder'] = str((path/Path(entry['config']).stem).resolve())
        else:
            data = [load_run(path)]
        self.pause()
        self.data, self.ci, self.bi, self.step, self.time = data, 0, min(1, len(data[0]['records'])-1), 0, 0
        self.case_box.configure(values=[r['description'] for r in data])
        self.case_box.current(0)
        self.populate_bundles()
        self.footer.set(f'已載入 {len(data)} 組案例。結果位置：{path.resolve()}')
        self.draw()

    def open_results(self):
        path = filedialog.askdirectory(title='選擇含 manifest.json 的實驗套件，或含 results.json 的單次結果')
        if path:
            try:
                self.load_results(path)
            except (OSError, ValueError, KeyError) as error:
                messagebox.showerror('結果載入失敗', str(error))

    def choose_config(self):
        path = filedialog.askopenfilename(title='選擇案例 JSON', initialdir=ROOT/'configs', filetypes=[('JSON', '*.json')])
        if path:
            self.config.set(path)

    def populate_bundles(self):
        self.bundle_box.configure(values=[f"{r['bundle']['id']}：{r['bundle']['source']} → {r['bundle']['dest']}" for r in self.run['records']])
        self.bundle_box.current(self.bi)

    def change_case(self, _=None):
        self.pause()
        self.ci, self.bi, self.step, self.time = self.case_box.current(), 0, 0, 0
        self.populate_bundles()
        self.draw()

    def change_bundle(self, _=None):
        self.pause()
        self.bi, self.step = self.bundle_box.current(), 0
        self.draw()

    def change_mode(self, _=None):
        self.pause()
        self.draw()

    def pause(self):
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.play_button.configure(text='播放')

    def move(self, direction, automatic=False):
        if not self.data:
            return
        if not automatic:
            self.pause()
        if self.searching:
            self.step = max(0, min(len(self.events())-1, self.step+direction))
        else:
            self.time = max(0, min(number(self.run['horizon']), self.time+.25*direction))
        self.draw()

    def play(self):
        if not self.data:
            return
        if self.timer:
            self.pause()
            return
        if (self.searching and self.step == len(self.events())-1) or (not self.searching and self.time == number(self.run['horizon'])):
            self.step, self.time = 0, 0
        self.play_button.configure(text='暫停')
        self.timer = self.root.after(50, self.tick)

    def tick(self):
        self.timer = None
        self.move(1, automatic=True)
        end = self.step == len(self.events())-1 if self.searching else self.time == number(self.run['horizon'])
        if end:
            self.pause()
        else:
            self.timer = self.root.after(1100 if self.searching else 250, self.tick)

    def seek(self, value):
        if self.updating or not self.data:
            return
        self.pause()
        if self.searching:
            self.step = max(0, min(len(self.events())-1, round(float(value))))
        else:
            self.time = float(value)
        self.draw()

    def draw(self):
        if not self.data:
            return
        self.updating = True
        self.scale.configure(to=len(self.events())-1 if self.searching else number(self.run['horizon']), resolution=1 if self.searching else .25)
        self.scale.set(self.step if self.searching else self.time)
        self.bundle_box.configure(state='readonly' if self.searching else 'disabled')
        if self.searching:
            event = self.events()[self.step]
            title, detail = event_text(self.run, self.record, event)
            self.status.set(title)
            self.detail.set(detail)
            self.position.set(f'步驟 {self.step+1} / {len(self.events())}')
            self.queue_text.set(f"Q：{event.get('queue_before', [])} → {event.get('queue_after', [])}")
            self.queue.delete(*self.queue.get_children())
            active = {'L0'}
            for e in self.events()[:self.step+1]:
                if e.get('new_label') and not e.get('dominated_by'):
                    active.add(e['new_label'])
                active.difference_update(e.get('removed', []))
            for lid in event.get('queue_after', []):
                l = self.record['labels'][lid]
                self.queue.insert('', 'end', values=(lid if lid in active else lid+'（失效）', l['node'], l['c'] or '—', l['A'], l['s'] or ('0' if l['s'] == '0' else '—'), l['pred'] or '—'))
            self.bundle_status.set('搜尋步數不代表實際時間；候選路徑尚未預約資源。')
        else:
            self.position.set(f'第 {self.time:g} 秒')
            tx = [s for s in self.run['schedules'] if number(s['start']) <= self.time < number(s['finish'])]
            self.status.set('；'.join(f"{s['bundle']} 經 {s['contact']} 發送" for s in tx) or '目前沒有發送中的已接受傳輸')
            self.detail.set('同 Contact 傳輸時段重疊：總容量模型接受，不代表實體鏈路可執行。' if self.run['conflicts'] else '依已接受排程重播；事件時刻顯示交付前峰值，再釋放。')
            self.queue_text.set('已接受排程模式：Q 不適用')
            self.queue.delete(*self.queue.get_children())
            states = []
            for r in self.run['records']:
                rows = [s for s in self.run['schedules'] if s['bundle'] == r['bundle']['id']]
                state = '未生成'
                if r['arrival'] is None:
                    state = '未接受（無路徑）'
                elif self.time > number(r['arrival']):
                    state = '已交付'
                elif self.time == number(r['arrival']):
                    state = '完整抵達，顯示交付前峰值'
                elif self.time >= number(r['bundle']['g']):
                    states_now = [f"經 {s['contact']} 發送" for s in rows if number(s['start']) <= self.time < number(s['finish'])]
                    states_now += [f"{s['receiver']} 接收" for s in rows if number(s['receive_start']) <= self.time < number(s['arrival'])]
                    state = '、'.join(states_now) or '持有整包，等待下一跳'
                states.append(r['bundle']['id']+'：'+state)
            self.bundle_status.set('\n'.join(states))
        self.contacts.delete(*self.contacts.get_children())
        self.contact_heading.set('Contact Plan（本次搜尋開始前的剩餘容量）' if self.searching else 'Contact Plan（全部接受排程後的剩餘容量）')
        for c in self.run['contacts']:
            # Recover aggregate quota from earlier accepted routes, including repeated contacts.
            if self.searching:
                used = sum(number(r['bundle']['size']) for r in self.run['records'][:self.bi] for cid, _ in r['hops'] if cid == c['id'])
                quota = number(c['quota'])-used
            else:
                quota = number(c['quota'])-sum(number(r['bundle']['size']) for r in self.run['records'] for cid, _ in r['hops'] if cid == c['id'])
            self.contacts.insert('', 'end', values=(c['id'], c['u']+'→'+c['v'], f"{c['start']}–{c['end']}", c['rate'], c['delay'], f'{number(quota):g}'))
        self.draw_graph()
        self.draw_buffers()
        self.root.update_idletasks()
        self.updating = False

    def draw_graph(self):
        canvas = self.graph
        canvas.delete('all')
        if not self.data:
            return
        w, h = max(340, canvas.winfo_width()), max(260, canvas.winfo_height())
        nodes, contacts = list(self.run['buffers']), self.run['contacts']
        if set(nodes) == {'X', 'A', 'B', 'C', 'D'}:
            pos = {'X':(.12*w,.2*h), 'A':(.12*w,.8*h), 'B':(.5*w,.25*h), 'C':(.5*w,.8*h), 'D':(.88*w,.5*h)}
        elif len(nodes) <= 3:
            pos = {n:((i+1)*w/(len(nodes)+1), h/2) for i,n in enumerate(nodes)}
        else:
            pos = {n:(w/2+.37*w*math.cos(2*math.pi*i/len(nodes)),h/2+.35*h*math.sin(2*math.pi*i/len(nodes))) for i,n in enumerate(nodes)}
        event = self.events()[self.step] if self.searching else {}
        path, lid = [], event.get('selected')
        while lid is not None:
            label = self.record['labels'][lid]
            if label['c']:
                path.append(label['c'])
            lid = label['pred']
        for c in contacts:
            x1,y1 = pos[c['u']]
            x2,y2 = pos[c['v']]
            length = math.hypot(x2-x1,y2-y1)
            ux,uy = (x2-x1)/length,(y2-y1)/length
            peers = [e for e in contacts if e['u']==c['u'] and e['v']==c['v']]
            offset = (peers.index(c)-(len(peers)-1)/2)*55
            mx,my = (x1+x2)/2-uy*offset,(y1+y2)/2+ux*offset
            active = event.get('contact') == c['id'] if self.searching else any(s['contact']==c['id'] and number(s['start'])<=self.time<number(s['finish']) for s in self.run['schedules'])
            color = '#c33535' if active and (event.get('reason', 'PASS')!='PASS' or 'FAIL' in event.get('event','')) else '#2168b3' if active else '#ca710b' if c['id'] in path and self.searching else '#b8c0c8'
            canvas.create_line(x1+ux*23,y1+uy*23,mx,my,x2-ux*25,y2-uy*25,smooth=True,arrow='last',fill=color,width=3 if active else 2)
            canvas.create_text(mx-uy*9,my+ux*9-9,text=c['id'],font=('標楷體',13),fill='#293846')
        selected = self.record['labels'].get(event.get('selected'), {}).get('node')
        for n,(x,y) in pos.items():
            canvas.create_oval(x-22,y-22,x+22,y+22,fill='#ffffff',outline='#2168b3' if n==selected else '#81909d',width=3 if n==selected else 1)
            canvas.create_text(x,y,text=n,font=('標楷體',15),fill='#172c3d')

    def draw_buffers(self):
        canvas = self.buffer_canvas
        canvas.delete('all')
        if not self.data:
            return
        w = max(250, canvas.winfo_width())
        if self.searching:
            canvas.configure(scrollregion=(0,0,w,100))
            canvas.create_text(12,15,anchor='nw',text='Buffer 檢查結果見上方說明。\n切換「已接受排程」可查看各時刻占用。',font=('標楷體',12),fill='#293846',width=w-24)
            return
        y = 12
        for node, capacity in self.run['buffers'].items():
            used = sum(curve_value(curve,self.time) for curve in self.run['occupancy'].get(node,[]))
            cap = number(capacity)
            canvas.create_text(12,y,anchor='nw',text=f'{node}：{used:g} / {cap:g} MB',font=('標楷體',12),fill='#293846')
            canvas.create_rectangle(12,y+23,w-12,y+33,fill='#e6ebef',outline='')
            if used:
                canvas.create_rectangle(12,y+23,12+(w-24)*min(1,used/cap if cap else 0),y+33,fill='#2168b3',outline='')
            y += 45
        canvas.configure(scrollregion=(0,0,w,y))

    def start_run(self):
        if self.process:
            return
        self.pause()
        path = Path(self.config.get())
        if not path.is_file():
            messagebox.showerror('找不到設定', str(path))
            return
        self.output = ROOT/'output/experiments/gui_runs'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        logs = ROOT/'output/experiments/gui_logs'
        logs.mkdir(parents=True, exist_ok=True)
        self.log_path = logs/(self.output.name+'.log')
        self.log = self.log_path.open('w',encoding='utf8')
        executable = str(Path(sys.executable).with_name('python.exe')) if Path(sys.executable).name.lower()=='pythonw.exe' else sys.executable
        command = [executable,'-m','src.experiments.gui','--worker',str(path.resolve()),str(self.output)]
        if self.oracle.get():
            command.append('--oracle')
        try:
            self.process = subprocess.Popen(command,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT,
                env={**os.environ,'PYTHONIOENCODING':'utf-8'},creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        except OSError as error:
            self.log.close()
            self.log = None
            messagebox.showerror('無法啟動',str(error))
            return
        self.run_button.configure(state='disabled')
        self.cancel_button.configure(state='normal')
        self.footer.set('執行中；完整搜尋可能耗時，可用「停止執行」中止。'+str(self.output))
        self.poll_timer = self.root.after(150,self.poll)

    def poll(self):
        self.poll_timer = None
        if not self.process:
            return
        code = self.process.poll()
        if code is None:
            self.poll_timer = self.root.after(150,self.poll)
            return
        self.log.close()
        self.log, self.process = None, None
        self.run_button.configure(state='normal')
        self.cancel_button.configure(state='disabled')
        if code == 0:
            try:
                self.load_results(self.output)
                self.footer.set('執行完成，已載入路徑與過程。'+str(self.output))
            except (OSError,ValueError,KeyError) as error:
                messagebox.showerror('結果載入失敗',str(error))
        else:
            self.footer.set('執行停止；輸出與錯誤紀錄已保留。'+str(self.log_path))
            messagebox.showerror('執行停止', self.log_path.read_text(encoding='utf8')[-2500:])

    def cancel_run(self):
        if not self.process:
            return
        if self.poll_timer:
            self.root.after_cancel(self.poll_timer)
            self.poll_timer = None
        running = self.process.poll() is None
        if running:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.log.close()
        self.log, self.process = None, None
        if running and self.output.exists():
            from .runner import write_json
            write_json(self.output/'gui_cancelled.json',dict(status='CANCELLED',partial_results=True))
        self.run_button.configure(state='normal')
        self.cancel_button.configure(state='disabled')
        self.footer.set('已停止。部分輸出保留，勿當成完成實驗。'+str(self.output))

    def close(self):
        self.pause()
        self.cancel_run()
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description='Space DTN 桌面實驗 GUI')
    parser.add_argument('--suite',type=Path,default=DEFAULT_SUITE)
    parser.add_argument('--worker',nargs=2,metavar=('CONFIG','OUTPUT'))
    parser.add_argument('--oracle',action='store_true')
    args = parser.parse_args()
    if args.worker:
        from .config import load_scenario
        from .runner import run_scenario
        from .report import generate
        try:
            run_scenario(load_scenario(args.worker[0]),args.worker[1],verify_oracle=args.oracle)
            generate(args.worker[1],draw=False)
        except Exception as error:
            print(f'停止：{error}',file=sys.stderr)
            return 2
        print('完成路由與獨立排程重播。')
        return 0
    enable_dpi_awareness()
    root = tk.Tk()
    ExperimentGUI(root,args.suite)
    root.mainloop()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
