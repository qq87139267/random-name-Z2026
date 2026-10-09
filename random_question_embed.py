import tkinter as tk
from tkinter import messagebox
import json, os, time, random
from ctypes import windll

HAS_WIN_API = True
NORMAL_ALPHA = 1.0
TRANS_ALPHA = 0.2  # 80%透明
IDLE_LIMIT = 8    # 8秒无操作变透明
DATA_FILE = "rollcall_data.json"

class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍌 下一位~~就你~~~ ✨")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0a0f1c")

        # 置顶+透明层
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
        self.drawn = []       # 记录已抽名单（备用）
        self.running = False
        self.last_active = time.time()
        self.load_data()

        # 字体适配
        self.font_class = ("STXingkai", 28, "bold")
        self.font_name = ("STXingkai", 72, "bold")
        self.font_btn = ("微软雅黑", 11, "bold")

        self.build_ui()
        self.update_class_ui()
        self.reset_remaining()
        self.tick()

        # 主界面点击：名字区域+空白区都能触发开始/停止
        self.root.bind("<Button-1>", self.on_click_root)
        self.name_label.bind("<Button-1>", self.toggle_roll)
        self.root.bind("<space>", self.toggle_roll)
        # 已移除 Esc 换班绑定
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Motion>", self.wake_up)

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

    def build_ui(self):
        self.class_label = tk.Label(self.root, text="", font=self.font_class, fg="#00ffff", bg="#0a0f1c")
        self.class_label.pack(pady=(30, 5))

        self.name_label = tk.Label(self.root, text="点击开始", font=self.font_name, fg="#ffd700", bg="#0a0f1c")
        self.name_label.pack(expand=True, fill="both", pady=10)

        # 底部按钮区：仅保留 开始/停止 + 重置
        btn_frame = tk.Frame(self.root, bg="#0a0f1c")
        btn_frame.pack(fill="x", pady=15, padx=40)

        self.toggle_btn = tk.Button(btn_frame, text="开始 (空格)", font=self.font_btn, bg="#27ae60", fg="white", command=self.toggle_roll)
        self.toggle_btn.pack(side="left", expand=True, fill="x", padx=5)

        self.reset_btn = tk.Button(btn_frame, text="重置", font=self.font_btn, bg="#e67e22", fg="white", command=self.reset_remaining)
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=5)

    def update_class_ui(self):
        cls = self.classes[self.current_idx]
        self.class_label.config(text=f"【{cls}】 共{len(self.data.get(cls, []))}人")

    def on_click_root(self, e):
        # 防止点按钮时重复触发
        if e.widget != self.root and e.widget.master != self.root:
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
        self.running = True
        self.toggle_btn.config(text="停止", bg="#c0392b")
        self.roll_tick()

    def stop_roll(self):
        self.running = False
        if self.remaining:
            name = self.remaining.pop(0)
            self.drawn.append(name)
        else:
            name = "抽完啦"
        self.name_label.config(text=name, fg="#ffd700")
        self.toggle_btn.config(text="开始 (空格)", bg="#27ae60")
        self.wake_up()

    def roll_tick(self):
        if not self.running:
            return
        if self.remaining:
            name = random.choice(self.remaining)
            self.name_label.config(text=name, fg="#ffffff")
        self.root.after(80, self.roll_tick)

    def reset_remaining(self):
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
