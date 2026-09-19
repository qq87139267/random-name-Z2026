import os
import glob
import random
import tkinter as tk
import tkinter.font as tkfont

# ================== 配置 ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_COLOR = "#1a1a2e"
ACCENT = "#4facfe"
BTN_BG = "#16213e"
BTN_FG = "#eaeaea"

_CANDIDATE_FONTS = ["华文行草", "华文行楷", "华文草书", "楷体", "微软雅黑"]


def _pick_font(size):
    try:
        available = tkfont.families()
        for f in _CANDIDATE_FONTS:
            if f in available:
                return (f, size)
        return ("微软雅黑", size)
    except Exception:
        return ("微软雅黑", size)


class RandomNameApp:
    def __init__(self, root):
        self.root = root
        root.title("💪 → 下一位~~就你啦 ~~~👉")
        # 真全屏
        root.attributes("-fullscreen", True)
        root.configure(bg=BG_COLOR)
        root.attributes("-topmost", True)

        self.classes = {}
        self.current_class = "默认"
        self.current_idx = 0
        self.pool = []
        self.used = []
        self.running = False
        self.roll_timer = None
        self._roll_count = 0

        self._load_classes()
        self.class_keys = list(self.classes.keys())
        if self.class_keys:
            self.current_class = self.class_keys[0]
            self.pool = list(self.classes[self.current_class])

        self.title_var = tk.StringVar(value=self.current_class)
        self.name_var = tk.StringVar(value="准备")

        # 顶部标题（点击换班）
        title_frame = tk.Frame(root, bg=BG_COLOR)
        title_frame.pack(pady=(15, 5))
        self.title_label = tk.Label(
            title_frame, textvariable=self.title_var,
            font=_pick_font(36), fg=ACCENT, bg=BG_COLOR, cursor="hand2"
        )
        self.title_label.pack()
        self.title_label.bind("<Button-1>", lambda e: self._switch_class())

        # 显示区
        display_frame = tk.Frame(
            root, bg=BG_COLOR, highlightthickness=2, highlightbackground="#333"
        )
        display_frame.pack(expand=True, fill="both", padx=40, pady=20)

        # 名字字体放大到120（全屏可见）
        self.name_label = tk.Label(
            display_frame, textvariable=self.name_var,
            font=_pick_font(120), fg="#ffffff", bg=BG_COLOR, cursor="hand2"
        )
        self.name_label.place(relx=0.5, rely=0.5, anchor="center")
        self.name_label.bind("<Button-1>", lambda e: self._toggle())

        # 进度
        self.progress = tk.Label(
            root, text="", font=_pick_font(20), fg="#aaa", bg=BG_COLOR
        )
        self.progress.pack(pady=5)
        self._update_progress()

        # 按钮区
        btn_frame = tk.Frame(root, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(
            btn_frame, text="开始", font=("微软雅黑", 14, "bold"),
            width=6, height=2, command=self._toggle,
            bg=ACCENT, fg="#1a1a2e", relief="flat"
        )
        self.start_btn.pack(side="left", padx=6)

        tk.Button(
            btn_frame, text="重置", font=("微软雅黑", 14), width=6, height=2,
            command=self._reset, bg=BTN_BG, fg=BTN_FG,
            relief="flat", activebackground="#1a3a5c"
        ).pack(side="left", padx=6)

        tk.Button(
            btn_frame, text="换班", font=("微软雅黑", 14), width=6, height=2,
            command=self._switch_class, bg=BTN_BG, fg=BTN_FG,
            relief="flat", activebackground="#1a3a5c"
        ).pack(side="left", padx=6)

        # 快捷键
        root.bind("<space>", lambda e: self._toggle())
        root.bind("<Escape>", lambda e: self._switch_class())
        root.bind("<BackSpace>", lambda e: self._reset())
        # 双击退出全屏
        root.bind("<Double-Button-1>", lambda e: root.attributes("-fullscreen", False))

        hint = tk.Label(
            root,
            text="点击名字:开始/停止 | 点击标题或[换班]:换班 | [重置]:重抽 | 双击:退出全屏",
            font=("微软雅黑", 10), fg="#555", bg=BG_COLOR
        )
        hint.pack(pady=(5, 0))

    def _load_classes(self):
        pattern = os.path.join(BASE_DIR, "class*.txt")
        files = sorted(glob.glob(pattern))
        if not files:
            self.classes["默认"] = ["张三", "李四", "王五", "赵六"]
            return
        for fpath in files:
            fname = os.path.basename(fpath)
            stem = os.path.splitext(fname)[0]
            class_id = stem.replace("class", "") or "1"
            class_name = f"{class_id}班" if class_id.isdigit() else stem
            names = []
            for encoding in ("utf-8", "gbk"):
                try:
                    with open(fpath, "r", encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                names.append(line)
                    break
                except (UnicodeDecodeError, OSError):
                    continue
            if names:
                self.classes[class_name] = names
        if not self.classes:
            self.classes["默认"] = ["张三", "李四", "王五", "赵六"]

    def _update_progress(self):
        if self.class_keys:
            total = len(self.classes[self.current_class])
            remaining = len(self.pool)
            self.progress.config(text=f"剩余 {remaining}/{total}")

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        if not self.pool:
            self.pool = list(self.classes[self.current_class])
            self.used = []
        self.running = True
        self.start_btn.config(text="停止", bg="#ef5350", fg="white")
        self.name_label.config(fg="#ff4d4f")
        self._roll_count = 0
        self._roll()

    def _roll(self):
        if not self.running:
            return
        if self.pool:
            self.name_var.set(random.choice(self.pool))
        self.roll_timer = self.root.after(80, self._roll)
        self._roll_count += 1
        if self._roll_count >= 25:
            self._auto_stop()

    def _stop(self):
        self.running = False
        self.start_btn.config(text="开始", bg=ACCENT, fg="#1a1a2e")
        if self.roll_timer:
            self.root.after_cancel(self.roll_timer)
            self.roll_timer = None
        self._update_progress()

    def _auto_stop(self):
        self.running = False
        self.start_btn.config(text="开始", bg=ACCENT, fg="#1a1a2e")
        if self.roll_timer:
            self.root.after_cancel(self.roll_timer)
            self.roll_timer = None

        chosen = self.name_var.get()
        if chosen in self.pool:
            self.pool.remove(chosen)
            self.used.append(chosen)

        if not self.pool:
            self.name_label.config(fg="#ff4d4f")
        else:
            self.name_label.config(fg="#ffd700")

        self._update_progress()

    def _switch_class(self):
        if not self.class_keys:
            return
        self.current_idx = (self.current_idx + 1) % len(self.class_keys)
        self.current_class = self.class_keys[self.current_idx]
        self.title_var.set(self.current_class)
        self.pool = list(self.classes[self.current_class])
        self.used = []
        self.name_var.set("准备")
        self.name_label.config(fg="#ffffff")
        self._stop()
        self._update_progress()

    def _reset(self):
        self.pool = list(self.classes[self.current_class])
        self.used = []
        self.name_var.set("准备")
        self.name_label.config(fg="#ffffff")
        self._stop()
        self._update_progress()


if __name__ == "__main__":
    root = tk.Tk()
    app = RandomNameApp(root)
    root.mainloop()
