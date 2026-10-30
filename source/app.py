"""Windows graphical launcher for the reviewed, version-locked localization."""
import csv
import json
import queue
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
from patch_engine import PatchError,install,restore
from release_bundle import prepare_install_bundle,restore_bundle,check_release

BASE=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
DATA=BASE/'data'

def load_resources():
    with (DATA/'game_profile.json').open(encoding='utf-8') as f:profile=json.load(f)
    with (DATA/'release_checklist.json').open(encoding='utf-8') as f:checks=json.load(f)
    with (DATA/'待译文本.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    font=(DATA/'fonts/fusion-pixel-proportional-zh-Hans-12px-square.ttf').read_bytes()
    license_data=(DATA/'fonts/OFL.txt').read_bytes()
    card_module=(DATA/'game_patch/zh_card_text.lua').read_bytes()
    return profile,checks,rows,font,license_data,card_module

class Application:
    def __init__(self,root,*,candidate=False):
        self.candidate=candidate
        self.root=root;self.root.title('Your Painting, Sir 试玩版汉化工具' + ('（测试版）' if candidate else ''))
        self.root.geometry('620x365');self.root.minsize(570,350)
        self.root.configure(background='#f5f2ec')
        self.path=tk.StringVar();self.status=tk.StringVar(value='选择游戏的 EXE 文件后开始。')
        self.events=queue.Queue();self.busy=False
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('Page.TFrame',background='#f5f2ec')
        style.configure('Title.TLabel',background='#f5f2ec',foreground='#252d33',font=('Microsoft YaHei UI',16,'bold'))
        style.configure('Body.TLabel',background='#f5f2ec',foreground='#50585d',font=('Microsoft YaHei UI',9))
        style.configure('Primary.TButton',font=('Microsoft YaHei UI',10,'bold'),padding=(15,9))
        style.configure('Action.TButton',font=('Microsoft YaHei UI',9),padding=(10,8))
        style.configure('Horizontal.TProgressbar',background='#267f77',troughcolor='#e6e2d9',borderwidth=0)
        page=ttk.Frame(root,style='Page.TFrame',padding=(24,20));page.pack(fill='both',expand=True)
        heading='Your Painting, Sir 试玩版汉化' + (' · 测试版' if candidate else '')
        subtitle='简体中文 · DEMO-1.2.16' + (' · 部分场景尚未完成验收' if candidate else '')
        ttk.Label(page,text=heading,style='Title.TLabel').pack(anchor='w')
        ttk.Label(page,text=subtitle,style='Body.TLabel').pack(anchor='w',pady=(5,18))
        ttk.Label(page,text='游戏程序',style='Body.TLabel').pack(anchor='w',pady=(0,5))
        row=ttk.Frame(page,style='Page.TFrame');row.pack(fill='x')
        self.entry=ttk.Entry(row,textvariable=self.path,font=('Microsoft YaHei UI',9));self.entry.pack(side='left',fill='x',expand=True,ipady=4)
        self.browse=ttk.Button(row,text='选择文件…',command=self.choose,style='Action.TButton');self.browse.pack(side='left',padx=(9,0))
        ttk.Label(page,text='选择游戏文件夹里的 Your Painting, Sir.exe',style='Body.TLabel').pack(anchor='w',pady=(5,15))
        actions=ttk.Frame(page,style='Page.TFrame');actions.pack(fill='x')
        self.start=ttk.Button(actions,text='开始汉化',command=lambda:self.begin('install'),style='Primary.TButton');self.start.pack(side='left')
        self.restore=ttk.Button(actions,text='恢复英文版',command=lambda:self.begin('restore'),style='Action.TButton');self.restore.pack(side='left',padx=10)
        self.bar=ttk.Progressbar(page,mode='indeterminate');self.bar.pack(fill='x',pady=(18,6))
        ttk.Label(page,textvariable=self.status,style='Body.TLabel',wraplength=545).pack(anchor='w')
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(80,self.pump)

    def choose(self):
        initial=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Your Painting, Sir Demo')
        name=filedialog.askopenfilename(parent=self.root,title='选择游戏 EXE',initialdir=str(initial) if initial.is_dir() else str(Path.home()),
                                        filetypes=[('Windows 程序','*.exe')])
        if name:self.path.set(name)

    def close(self):
        if self.busy:
            messagebox.showinfo('正在处理','请等待当前操作完成，避免中断文件处理。',parent=self.root)
        else:self.root.destroy()

    def begin(self,action):
        if self.busy:return
        target=self.path.get().strip().strip('"')
        if not target:
            messagebox.showwarning('请选择游戏','请先选择 Your Painting, Sir.exe。',parent=self.root);return
        self.busy=True
        for widget in (self.entry,self.browse,self.start,self.restore):widget.state(['disabled'])
        self.status.set('正在准备…');self.bar.start(12)
        threading.Thread(target=self.worker,args=(action,target),daemon=True).start()

    def worker(self,action,target):
        def progress(text):self.events.put(('progress',text))
        try:
            profile,checks,rows,font,license_data,card_module=load_resources()
            if action=='install':
                bundle=prepare_install_bundle(target,profile,rows,checks,font,license_data,card_module,progress=progress,candidate=self.candidate)
                result=install(target,bundle,progress=progress)
            else:
                result=restore(target,restore_bundle(profile),progress=progress)
            self.events.put(('done',result))
        except PatchError as e:self.events.put(('error',str(e)))
        except Exception as e:self.events.put(('error','工具无法完成操作：'+str(e)))

    def pump(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='progress':self.status.set(value);continue
                self.busy=False;self.bar.stop()
                for widget in (self.entry,self.browse,self.start,self.restore):widget.state(['!disabled'])
                if kind=='error':
                    self.status.set('未完成。请根据提示检查后重试。')
                    messagebox.showerror('操作未完成',value,parent=self.root)
                else:
                    messages={
                        'installed':'汉化完成。现在可以从 Steam 启动游戏。',
                        'already_installed':'检测到已安装的汉化，无需重复安装。',
                        'restored':'已恢复英文原版。',
                        'already_original':'当前已经是支持的英文原版。',
                    }
                    text=messages[value]
                    if self.candidate and value=='installed':
                        text='测试版汉化已安装。可以从 Steam 启动游戏；部分场景仍待完整验收。'
                    self.status.set(text);messagebox.showinfo('完成',text,parent=self.root)
        except queue.Empty:pass
        self.root.after(80,self.pump)

def main():
    if '--check-resources' in sys.argv:
        profile,checks,rows,_,_,_=load_resources()
        try:check_release(rows,checks)
        except PatchError as e:print(str(e));return 2
        print('发布资源检查通过：',profile['game_version']);return 0
    root=tk.Tk();Application(root);root.mainloop();return 0

if __name__=='__main__':raise SystemExit(main())
