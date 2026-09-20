import tkinter as tk
import json
import os
import random
import time
import sys

# 尝试导入置顶与透明度所需模块
try:
    import ctypes
    from ctypes import windll
    HAS_WIN_API = True
except ImportError:
    HAS_WIN_API = False

DATA_FILE = "rollcall_data.json"
IDLE_LIMIT = 20  # 20秒无操作
TRANS_ALPHA = 0.2  # 80%透明（即20%不透明度）
NORMAL_ALPHA = 1.0

# 默认数据
DEFAULT_DATA = {
    "426班": ["张三", "李四", "王五"],
    "427班": ["赵六", "钱七", "孙八"],
    "428班": ["周九", "吴十", "郑十一"]
}

class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💪下一位~~就係你~~~☝️↗")
        self.root.geometry("400x300")
        self.root.configure(bg="#1a1a2e")
        
        # 数据加载
        self.data = self.load_data()
        self.classes = list(self.data.keys())
        self.current_idx = 0
        self.remaining = []
        self.running = False
        self.last_active = time.time()
        
        # 字体栈
        self.font_title = ("华文行楷", "STXingkai", "楷体", "隶书", "微软雅黑")
        self.font_btn = ("微软雅黑", 12)
        
        self.build_ui()
        self.reset_remaining()
        
        # 系统级置顶
        if HAS_WIN_API:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0010)
            except Exception:
                pass
        
        # 事件绑定
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Space>", self.toggle_start)
        self.root.bind("<Escape>", self.switch_class)
        self.root.bind("<Button-1>", self.wake_up)
        self.root.bind("<Motion>", self.wake_up)
        
        self.tick()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_DATA

    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def build_ui(self):
        # 顶部：班级 + 管理按钮
        self.top_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.top_frame.pack(fill="x", padx=10, pady=10)
        
        self.class_label = tk.Label(self.top_frame, text="", fg="#00d4ff", bg="#1a1a2e", font=self.font_title)
        self.class_label.pack(side="left", padx=5)
        
        self.admin_frame = tk.Frame(self.top_frame, bg="#1a1a2e")
        self.admin_frame.pack(side="right")
        
        tk.Button(self.admin_frame, text="+ 新建班级", bg="#27ae60", fg="white", font=self.font_btn, command=self.add_class).pack(side="left", padx=3)
        tk.Button(self.admin_frame, text="- 删除当前班", bg="#e74c3c", fg="white", font=self.font_btn, command=self.del_class).pack(side="left", padx=3)
        tk.Button(self.admin_frame, text="✎ 编辑名单", bg="#e67e22", fg="white", font=self.font_btn, command=self.edit_names).pack(side="left", padx=3)
        
        # 悬停显示管理按钮（小窗口用）
        self.top_frame.bind("<Enter>", self.show_admin)
        self.top_frame.bind("<Leave>", self.hide_admin)
        
        # 中间：大字
        self.mid_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.mid_frame.pack(expand=True, fill="both")
        
        self.name_label = tk.Label(self.mid_frame, text="点击开始", fg="#ffd700", bg="#1a1a2e", font=self.font_title)
        self.name_label.pack(expand=True)
        
        self.remain_label = tk.Label(self.mid_frame, text="", fg="#cccccc", bg="#1a1a2e", font=("微软雅黑", 16))
        self.remain_label.pack(pady=10)
        
        # 底部：核心按钮
        self.bot_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.bot_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_btn = tk.Button(self.bot_frame, text="开始 / 停止 (空格)", bg="#3498db", fg="white", font=self.font_btn, command=self.toggle_start)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.reset_btn = tk.Button(self.bot_frame, text="重置", bg="#e67e22", fg="white", font=self.font_btn, command=self.reset_remaining)
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.switch_btn = tk.Button(self.bot_frame, text="换班 (Esc)", bg="#27ae60", fg="white", font=self.font_btn, command=self.switch_class)
        self.switch_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.update_class_ui()
        self.on_resize()

    def show_admin(self, e=None):
        if self.root.winfo_width() < 650:
            self.admin_frame.pack(side="right")

    def hide_admin(self, e=None):
        if self.root.winfo_width() < 650:
            self.admin_frame.pack_forget()

    def on_resize(self, e=None):
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        # 动态字体
        if w < 650:  # 小窗口
            self.class_label.config(font=(self.font_title[0], 32))
            self.name_label.config(font=(self.font_title[0], 80))
            self.start_btn.config(font=("微软雅黑", 12), padx=5)
            self.reset_btn.config(font=("微软雅黑", 12), padx=5)
            self.switch_btn.config(font=("微软雅黑", 12), padx=5)
            self.hide_admin()
        else:
            self.class_label.config(font=(self.font_title[0], 48))
            self.name_label.config(font=(self.font_title[0], 120))
            self.start_btn.config(font=self.font_btn, padx=10)
            self.reset_btn.config(font=self.font_btn, padx=10)
            self.switch_btn.config(font=self.font_btn, padx=10)
            self.admin_frame.pack(side="right")
        
        # 剩余人数
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{sum(len(v) for v in self.data.values())}")

    def update_class_ui(self):
        if not self.classes:
            self.classes = ["默认班"]
            self.data["默认班"] = ["示例"]
        cls = self.classes[self.current_idx]
        self.class_label.config(text=cls)
        self.remaining = list(self.data.get(cls, []))
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data.get(cls, []))}")

    def reset_remaining(self):
        cls = self.classes[self.current_idx]
        self.remaining = list(self.data.get(cls, []))
        self.name_label.config(text="点击开始", fg="#ffd700")
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data.get(cls, []))}")
        self.running = False

    def toggle_start(self, e=None):
        self.last_active = time.time()
        self.wake_up()
        if self.running:
            self.running = False
            return
        if not self.remaining:
            self.reset_remaining()
            return
        self.running = True
        self.roll()

    def roll(self):
        if not self.running:
            return
        name = random.choice(self.remaining)
        # 万花筒色彩
        colors = ["#ffd700", "#ff6b6b", "#4ecdc4", "#a29bfe", "#fd79a8", "#ffeaa7", "#55efc4"]
        c = random.choice(colors)
        self.name_label.config(text=name, fg=c)
        
        speed = 50 if self.running else 200
        self.root.after(speed, self.roll)
        # 3秒自动停
        if time.time() - self.last_active > 3 and self.running:
            self.stop_roll(name)

    def stop_roll(self, name):
        self.running = False
        self.remaining.remove(name) if name in self.remaining else None
        # 金色3D定格
        self.name_label.config(text=name, fg="#ffd700", font=(self.font_title[0], self.name_label.cget("font").split()[1] if w := self.name_label.cget("font") else 120, "bold"))
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data.get(self.classes[self.current_idx], []))}")

    def switch_class(self, e=None):
        self.last_active = time.time()
        self.wake_up()
        self.current_idx = (self.current_idx + 1) % len(self.classes)
        self.update_class_ui()
        self.reset_remaining()

    def add_class(self):
        top = tk.Toplevel(self.root)
        top.title("新建班级")
        tk.Label(top, text="班级名称:").pack(padx=10, pady=5)
        ent = tk.Entry(top)
        ent.pack(padx=10)
        def ok():
            n = ent.get().strip()
            if n and n not in self.data:
                self.data[n] = []
                self.classes.append(n)
                self.save_data()
                self.current_idx = len(self.classes)-1
                self.update_class_ui()
                self.reset_remaining()
            top.destroy()
        tk.Button(top, text="确定", command=ok).pack(pady=10)

    def del_class(self):
        cls = self.classes[self.current_idx]
        if len(self.classes) <= 1:
            return
        del self.data[cls]
        self.classes.remove(cls)
        self.current_idx = 0
        self.save_data()
        self.update_class_ui()
        self.reset_remaining()

    def edit_names(self):
        cls = self.classes[self.current_idx]
        top = tk.Toplevel(self.root)
        top.title(f"编辑名单 - {cls}")
        top.geometry("400x400")
        txt = tk.Text(top, font=("微软雅黑", 12))
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        txt.insert("1.0", "\n".join(self.data[cls]))
        def save():
            self.data[cls] = [l.strip() for l in txt.get("1.0", "end").splitlines() if l.strip()]
            self.save_data()
            self.reset_remaining()
            top.destroy()
        tk.Button(top, text="保存", command=save).pack(pady=5)

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
            # 80%透明
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
