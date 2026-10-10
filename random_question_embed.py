import tkinter as tk
from tkinter import messagebox
import json, os, time, random, subprocess
from ctypes import windll

HAS_WIN_API = True
NORMAL_ALPHA = 1.0
TRANS_ALPHA = 0.2
IDLE_LIMIT = 8
DATA_FILE = "rollcall_data.json"

class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍌💪下一位~~就係你~~~☝️↗ ✨")
        self.root.geometry("440x360")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0a0f1c")

        if HAS_WIN_API:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
                windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(NORMAL_ALPHA*255), 2)
            except Exception:
                pass

        self.data = {}
        self.classes = []
        self.current_idx = 0
        self.remaining = []
        self.drawn = []
        self.running = False
        self.last_active = time.time()
        self.voice_on = True
        self.load_data()

        self.font_class = ("STXingkai", 26, "bold")
        self.font_name = ("STXingkai", 72, "bold")
        self.font_btn = ("微软雅黑", 11, "bold")

        self.build_ui()
        self.update_class_ui()
        self.reset_remaining()
        self.tick()

        self.root.bind("<Button-1>", self.on_click_root)
        self.name_label.bind("<Button-1>", self.toggle_roll)
        self.root.bind("<space>", self.toggle_roll)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Motion>", self.wake_up)

    # ---------- 数据 ----------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.classes = list(self.data.keys())
            except Exception:
                self.data = {}
                self.classes = []
        if not self.classes:
            self.data["426班"] = []
            self.classes = ["426班"]
        self.current_idx = 0

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ---------- 系统默认 TTS（不强制粤语）----------
    def speak_name(self, name):
        """PowerShell + .NET TTS 系统默认播报"""
        if not self.voice_on:
            return
        text = f"请 {name} 同学响亮回答"
        ps_cmd = (
            'Add-Type -AssemblyName System.Speech; '
            '$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            '$s.Rate = 1; $s.Volume = 100; '
            f'$s.Speak("{text}")'
        )
        try:
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    # ---------- 界面 ----------
    def build_ui(self):
        top = tk.Frame(self.root, bg="#0a0f1c")
        top.pack(fill="x", padx=8, pady=(6, 2))

        self.class_label = tk.Label(top, text="", font=self.font_class, fg="#00ffff", bg="#0a0f1c")
        self.class_label.pack(side="left", padx=4)

        self.gear_btn = tk.Button(top, text="⚙", font=("微软雅黑", 18), bg="#0a0f1c", fg="#666666",
                                  bd=0, activebackground="#0a0f1c", activeforeground="#aaaaaa",
                                  cursor="hand2", command=self.pop_menu)
        self.gear_btn.pack(side="right", padx=4)

        self.name_label = tk.Label(self.root, text="点击开始", font=self.font_name, fg="#ffd700", bg="#0a0f1c")
        self.name_label.pack(expand=True, fill="both", pady=8)

        self.remain_label = tk.Label(self.root, text="", font=("微软雅黑", 11), fg="#888888", bg="#0a0f1c")
        self.remain_label.pack(pady=2)

        btn_frame = tk.Frame(self.root, bg="#0a0f1c")
        btn_frame.pack(fill="x", pady=(6, 12), padx=40)

        self.toggle_btn = tk.Button(btn_frame, text="开始 (空格)", font=self.font_btn, bg="#27ae60", fg="white", command=self.toggle_roll)
        self.toggle_btn.pack(side="left", expand=True, fill="x", padx=5)

        self.reset_btn = tk.Button(btn_frame, text="重置", font=self.font_btn, bg="#e67e22", fg="white", command=self.reset_remaining)
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=5)

    def pop_menu(self):
        self.wake_up()
        menu = tk.Menu(self.root, tearoff=0, font=("微软雅黑", 11),
                       bg="#1a1a2e", fg="white", activebackground="#3498db", activeforeground="white")
        menu.add_command(label="＋ 新建班级", command=self.add_class)
        menu.add_command(label="✎ 编辑名单", command=self.edit_names)
        menu.add_command(label="🗑 删除班级", command=self.del_class)
        menu.add_separator()
        menu.add_command(label="⏷ 切换班级", command=self.switch_class)
        menu.add_separator()
        menu.add_command(label="📋 已抽列表", command=self.show_drawn)
        menu.add_separator()
        voice_label = "🗣 语音：开" if self.voice_on else "🤐 语音：关"
        menu.add_command(label=voice_label, command=self.toggle_voice)
        menu.post(self.gear_btn.winfo_rootx(), self.gear_btn.winfo_rooty() + 30)

    def toggle_voice(self):
        self.voice_on = not self.voice_on

    def update_class_ui(self):
        if not self.classes:
            return
        cls = self.classes[self.current_idx]
        total = len(self.data.get(cls, []))
        self.class_label.config(text=f"{cls}")
        self.remain_label.config(text=f"共 {total} 人    剩余 {len(self.remaining)} 人")

    def on_click_root(self, e):
        if e.widget != self.root:
            return
        self.toggle_roll()

    def toggle_roll(self, e=None):
        if self.running:
            self.stop_roll()
        else:
            self.start_roll()
        self.wake_up()

    def start_roll(self):
        if not self.remaining:
            self.reset_remaining()
        if not self.remaining:
            self.name_label.config(text="名单为空", fg="#ff4444")
            return
        self.running = True
        self.toggle_btn.config(text="停止", bg="#c0392b")
        self.start_time = time.time()
        self.roll_tick()

    def roll_tick(self):
        if not self.running:
            return
        t = time.time() - self.start_time
        if t >= 3:
            self.stop_roll()
            return
        if self.remaining:
            name = random.choice(self.remaining)
            colors = ["#ffd700", "#ff4d4d", "#4dff88", "#4dabff", "#bf4dff", "#ff8c4d", "#4dffff"]
            self.name_label.config(text=name, fg=colors[int(t * 10) % len(colors)])
        delay = 60 if t < 2 else 130
        self.root.after(delay, self.roll_tick)

    def stop_roll(self):
        self.running = False
        if self.remaining:
            name = random.choice(self.remaining)
            self.remaining.remove(name)
            self.drawn.append(name)
            self.name_label.config(text=name, fg="#ffd700")
            self.root.after(100, lambda: self.speak_name(name))
        self.toggle_btn.config(text="开始 (空格)", bg="#27ae60")
        self.update_class_ui()
        self.wake_up()

    def add_class(self):
        top = tk.Toplevel(self.root)
        top.title("新建班级")
        top.geometry("300x160")
        top.grab_set()
        top.configure(bg="#0a0f1c")
        tk.Label(top, text="班级名称：", font=("微软雅黑", 11), fg="white", bg="#0a0f1c").pack(padx=12, pady=(16, 4))
        ent = tk.Entry(top, font=("微软雅黑", 12))
        ent.pack(padx=12, fill="x")
        ent.focus()
        def ok():
            name = ent.get().strip()
            if not name:
                messagebox.showwarning("提示", "班级名称不能为空", parent=top)
                return
            if name in self.data:
                messagebox.showwarning("提示", "该班级已存在", parent=top)
                return
            self.data[name] = []
            self.classes.append(name)
            self.current_idx = len(self.classes) - 1
            self.save_data()
            self.reset_remaining()
            top.destroy()
        tk.Button(top, text="确定", font=("微软雅黑", 11, "bold"), bg="#27ae60", fg="white", command=ok, padx=20).pack(pady=12)
        top.bind("<Return>", lambda e: ok())

    def del_class(self):
        if len(self.classes) <= 1:
            messagebox.showinfo("提示", "至少保留一个班级", parent=self.root)
            return
        cls = self.classes[self.current_idx]
        if not messagebox.askyesno("确认", f"确定删除班级「{cls}」？\n该班级名单将一并删除。", parent=self.root):
            return
        del self.data[cls]
        self.classes.remove(cls)
        self.current_idx = 0
        self.save_data()
        self.reset_remaining()

    def switch_class(self):
        if len(self.classes) <= 1:
            self.name_label.config(text="仅一个班")
            self.root.after(800, lambda: self.name_label.config(text="点击开始", fg="#ffd700"))
            return
        self.current_idx = (self.current_idx + 1) % len(self.classes)
        self.reset_remaining()
        self.wake_up()

    def edit_names(self):
        cls = self.classes[self.current_idx]
        top = tk.Toplevel(self.root)
        top.title(f"编辑名单 - {cls}")
        top.geometry("360x460")
        top.grab_set()
        top.configure(bg="#0a0f1c")
        tk.Label(top, text="每行写一个名字：", font=("微软雅黑", 10), fg="#cccccc", bg="#0a0f1c").pack(anchor="w", padx=12, pady=(12, 4))
        txt = tk.Text(top, font=("微软雅黑", 12), wrap="none")
        txt.pack(expand=True, fill="both", padx=12)
        txt.insert("1.0", "\n".join(self.data.get(cls, [])))
        txt.focus()
        def save():
            names = [l.strip() for l in txt.get("1.0", "end").splitlines() if l.strip()]
            seen, uniq = set(), []
            for n in names:
                if n not in seen:
                    seen.add(n)
                    uniq.append(n)
            self.data[cls] = uniq
            self.save_data()
            self.reset_remaining()
            top.destroy()
        btn_row = tk.Frame(top, bg="#0a0f1c")
        btn_row.pack(fill="x", padx=12, pady=10)
        tk.Button(btn_row, text="保存 (Ctrl+回车)", font=("微软雅黑", 10, "bold"), bg="#27ae60", fg="white", command=save).pack(side="left", expand=True, padx=4)
        tk.Button(btn_row, text="取消", font=("微软雅黑", 10), bg="#555555", fg="white", command=top.destroy).pack(side="left", expand=True, padx=4)
        top.bind("<Control-Return>", lambda e: save())
        top.bind("<Return>", lambda e: save())

    def show_drawn(self):
        cls = self.classes[self.current_idx]
        top = tk.Toplevel(self.root)
        top.title(f"已抽列表 - {cls}")
        top.geometry("300x400")
        top.configure(bg="#0a0f1c")
        tk.Label(top, text=f"已抽 {len(self.drawn)} 人：", font=("微软雅黑", 11, "bold"), fg="#ffd700", bg="#0a0f1c").pack(pady=10)
        txt = tk.Text(top, font=("微软雅黑", 12), bg="#1a1a2e", fg="white", wrap="none")
        txt.pack(expand=True, fill="both", padx=12, pady=(0, 12))
        if self.drawn:
            for i, name in enumerate(self.drawn, 1):
                txt.insert("end", f"{i}. {name}\n")
        else:
            txt.insert("end", "（暂无已抽记录）")
        txt.config(state="disabled")

    def reset_remaining(self):
        if not self.classes:
            return
        cls = self.classes[self.current_idx]
        self.remaining = self.data.get(cls, [])[:]
        self.drawn = []
        self.running = False
        self.name_label.config(text="点击开始", fg="#ffd700")
        self.toggle_btn.config(text="开始 (空格)", bg="#27ae60")
        self.update_class_ui()

    def on_resize(self, e):
        self.wake_up()

    def wake_up(self, e=None):
        self.last_active = time.time()
        if HAS_WIN_API:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(NORMAL_ALPHA*255), 2)
            except Exception:
                pass
        self.root.attributes("-alpha", NORMAL_ALPHA)

    def tick(self):
        idle = time.time() - self.last_active
        if idle >= IDLE_LIMIT and not self.running:
            if HAS_WIN_API:
                try:
                    hwnd = windll.user32.GetParent(self.root.winfo_id())
                    windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(TRANS_ALPHA*255), 2)
                except Exception:
                    pass
            self.root.attributes("-alpha", TRANS_ALPHA)
        self.root.after(500, self.tick)

if __name__ == "__main__":
    root = tk.Tk()
    app = RollCallApp(root)
    root.mainloop()
