import tkinter as tk
from tkinter import messagebox
import json, os, time, random
try:
    import windll, ctypes
    HAS_WIN_API = True
except Exception:
    HAS_WIN_API = False

DATA_FILE = "rollcall_data.json"
NORMAL_ALPHA = 1.0
TRANS_ALPHA = 0.2  # 80%透明（20%不透明度）
IDLE_LIMIT = 20
COMPACT_W = 650  # 小窗口阈值

class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💪 →下一位~~就係你~~~☝️↗")
        self.root.geometry("480x360")
        self.root.configure(bg="#1a1a2e")
        self.root.attributes("-topmost", True)
        if HAS_WIN_API:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                windll.user32.SetWindowLongW(hwnd, -20, 0x80000|0x20)
                windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 2)
            except Exception:
                pass

        self.data = {"426班": ["蔡家乐", "张三", "李四"]}
        self.classes = ["426班"]
        self.current_idx = 0
        self.remaining = self.data["426班"][:]
        self.running = False
        self.last_active = time.time()
        self.colors = ["#ff0000","#ff7f00","#ffff00","#00ff00","#00ffff","#0000ff","#8b00ff","#ff1493","#ffd700","#00fa9a","#ff69b4","#1e90ff"]
        self.color_idx = 0
        self._stop_timer = None

        self._build_ui()
        self.load_data()
        self.update_class_ui()
        self.wake_up()
        self.tick()
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<space>", lambda e: self.toggle_roll())
        self.root.bind("<Escape>", lambda e: self.switch_class())
        self.root.bind("<Button-1>", lambda e: self.wake_up())
        self.root.bind("<Double-Button-1>", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))

    def _build_ui(self):
        # 顶部：班级名 + 管理区（大窗显示按钮，小窗仅显示⚙）
        self.top = tk.Frame(self.root, bg="#1a1a2e")
        self.top.pack(fill="x", padx=5, pady=2)
        self.class_label = tk.Label(self.top, text="426班", fg="#00ffff", bg="#1a1a2e", font=("STXingkai", 28, "bold"))
        self.class_label.pack(side="left", padx=5)
        self.admin_frame = tk.Frame(self.top, bg="#1a1a2e")
        self.admin_frame.pack(side="right", padx=2)
        # 大窗按钮（紧凑）
        self.btn_new = tk.Button(self.admin_frame, text="+新建", command=self.add_class, bg="#28a745", fg="white", font=("微软雅黑", 10), padx=5, pady=2)
        self.btn_del = tk.Button(self.admin_frame, text="-删除", command=self.del_class, bg="#dc3545", fg="white", font=("微软雅黑", 10), padx=5, pady=2)
        self.btn_edit = tk.Button(self.admin_frame, text="✎编辑", command=self.edit_names, bg="#fd7e14", fg="white", font=("微软雅黑", 10), padx=5, pady=2)
        # 小窗极简按钮（默认隐藏）
        self.btn_mini = tk.Button(self.admin_frame, text="⚙", command=self.pop_admin, bg="#444", fg="white", font=("微软雅黑", 12, "bold"), width=2, height=1)
        
        # 中部：名字显示
        self.mid = tk.Frame(self.root, bg="#1a1a2e")
        self.mid.pack(expand=True, fill="both", padx=5, pady=2)
        self.name_label = tk.Label(self.mid, text="点击开始", fg="#ffd700", bg="#1a1a2e", font=("STXingkai", 72, "bold"))
        self.name_label.pack(expand=True)
        self.remain_label = tk.Label(self.mid, text="剩余 3/3", fg="#cccccc", bg="#1a1a2e", font=("微软雅黑", 12))
        self.remain_label.pack(pady=2)

        # 底部：核心按钮（紧凑）
        self.bot = tk.Frame(self.root, bg="#1a1a2e")
        self.bot.pack(fill="x", padx=5, pady=5)
        self.btn_start = tk.Button(self.bot, text="开始/停止", command=self.toggle_roll, bg="#007bff", fg="white", font=("微软雅黑", 13, "bold"), padx=10, pady=5)
        self.btn_reset = tk.Button(self.bot, text="重置", command=self.reset_remaining, bg="#fd7e14", fg="white", font=("微软雅黑", 13), padx=10, pady=5)
        self.btn_swap = tk.Button(self.bot, text="换班(Esc)", command=self.switch_class, bg="#28a745", fg="white", font=("微软雅黑", 13), padx=10, pady=5)
        self._layout_buttons(large=False)

    def _layout_buttons(self, large):
        # 清理
        self.btn_new.pack_forget(); self.btn_del.pack_forget(); self.btn_edit.pack_forget(); self.btn_mini.pack_forget()
        self.btn_start.pack_forget(); self.btn_reset.pack_forget(); self.btn_swap.pack_forget()
        
        if large:
            # 大窗：顶部三个按钮显示，底部正常
            self.btn_new.pack(side="left", padx=3)
            self.btn_del.pack(side="left", padx=3)
            self.btn_edit.pack(side="left", padx=3)
            self.btn_start.pack(side="left", expand=True, fill="x", padx=5, pady=3)
            self.btn_reset.pack(side="left", expand=True, fill="x", padx=5, pady=3)
            self.btn_swap.pack(side="left", expand=True, fill="x", padx=5, pady=3)
            self.class_label.config(font=("STXingkai", 36, "bold"))
            self.name_label.config(font=("STXingkai", 100, "bold"))
        else:
            # 小窗：顶部仅⚙，底部压缩
            self.btn_mini.pack(side="right", padx=2)
            self.btn_start.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self.btn_reset.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self.btn_swap.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self.class_label.config(font=("STXingkai", 22, "bold"))
            self.name_label.config(font=("STXingkai", 60, "bold"))
            self.btn_start.config(font=("微软雅黑", 11, "bold"), padx=5, pady=3)
            self.btn_reset.config(font=("微软雅黑", 11), padx=5, pady=3)
            self.btn_swap.config(font=("微软雅黑", 11), padx=5, pady=3)

    def pop_admin(self):
        # 小窗点击⚙弹出管理菜单
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="新建班级", command=self.add_class)
        menu.add_command(label="删除当前班", command=self.del_class)
        menu.add_command(label="编辑名单", command=self.edit_names)
        menu.post(self.btn_mini.winfo_rootx(), self.btn_mini.winfo_rooty()+25)

    def on_resize(self, e=None):
        if not hasattr(self, 'root'): return
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        large = w >= COMPACT_W
        self._layout_buttons(large=large)
        self.wake_up()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                d = json.load(open(DATA_FILE, encoding="utf-8"))
                if d:
                    self.data = d
                    self.classes = list(d.keys())
                    self.current_idx = 0
                    self.remaining = self.data[self.classes[0]][:]
            except Exception:
                pass

    def save_data(self):
        json.dump(self.data, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def update_class_ui(self):
        cls = self.classes[self.current_idx]
        self.class_label.config(text=cls)
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data[cls])}")
        if not self.running:
            self.name_label.config(text="点击开始", fg="#ffd700")

    def toggle_roll(self):
        self.wake_up()
        if self.running:
            self.stop_roll()
        else:
            if not self.remaining:
                self.reset_remaining()
            self.running = True
            self._roll()

    def _roll(self):
        if not self.running: return
        self.color_idx = (self.color_idx + 1) % len(self.colors)
        name = random.choice(self.remaining)
        self.name_label.config(text=name, fg=self.colors[self.color_idx])
        # 速度：前2秒快，后1秒慢
        t = time.time() - self._start_t if hasattr(self, '_start_t') else 0
        if not hasattr(self, '_start_t'):
            self._start_t = time.time()
        delay = 80 if t < 2 else 180
        self.root.after(delay, self._roll)
        # 3秒自动停
        if t >= 3:
            self.stop_roll()

    def stop_roll(self):
        self.running = False
        self._start_t = None
        if self._stop_timer:
            self.root.after_cancel(self._stop_timer)
        name = self.name_label.cget("text")
        if name in self.remaining:
            self.remaining.remove(name)
        self._set_gold()
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data[self.classes[self.current_idx]])}")

    def _set_gold(self):
        # 干净封装金色定格
        self.name_label.config(fg="#ffd700", font=("STXingkai", self.name_label.cget("font").split()[1] if self.name_label.cget("font") else 72, "bold"))

    def reset_remaining(self):
        cls = self.classes[self.current_idx]
        self.remaining = self.data[cls][:]
        self.update_class_ui()

    def switch_class(self, e=None):
        self.wake_up()
        self.current_idx = (self.current_idx + 1) % len(self.classes)
        self.remaining = self.data[self.classes[self.current_idx]][:]
        self.update_class_ui()

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
                self.remaining = []
                self.update_class_ui()
            top.destroy()
        tk.Button(top, text="确定", command=ok).pack(pady=10)

    def del_class(self):
        cls = self.classes[self.current_idx]
        if len(self.classes) <= 1: return
        del self.data[cls]
        self.classes.remove(cls)
        self.current_idx = 0
        self.save_data()
        self.remaining = self.data[self.classes[0]][:]
        self.update_class_ui()

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
