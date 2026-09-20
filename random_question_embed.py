import tkinter as tk
from tkinter import messagebox
import json, os, time, random
from ctypes import windll

HAS_WIN_API = True
NORMAL_ALPHA = 1.0
TRANS_ALPHA = 0.2  # 80%透明
IDLE_LIMIT = 20
DATA_FILE = "rollcall_data.json"

class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💪 → 下一位～～就係你～～～ ✨↗")
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
        self.running = False
        self.last_active = time.time()
        self._load_data()

        # 字体适配
        self.font_class = ("STXingkai", 28, "bold")
        self.font_name = ("STXingkai", 72, "bold")
        self.font_btn = ("微软雅黑", 11, "bold")

        self._build_ui()
        self.update_class_ui()
        self.reset_remaining()
        self.tick()

        # 主界面点击：名字区域+空白区都能触发开始/停止
        self.root.bind("<Button-1>", self.on_click_root)
        self.name_label.bind("<Button-1>", self.toggle_roll)
        self.root.bind("<space>", self.toggle_roll)
        self.root.bind("<Escape>", lambda e: self.switch_class())
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Motion>", self.wake_up)
        self.root.bind("<Key>", self.wake_up)

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.classes = list(self.data.keys())
            except:
                self.data = {"426班": ["黄常乐","梁梦琪","梁耀文"]}
                self.classes = ["426班"]
        else:
            self.data = {"426班": ["黄常乐","梁梦琪","梁耀文"]}
            self.classes = ["426班"]

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        # 顶部
        self.top_frame = tk.Frame(self.root, bg="#0a0f1c")
        self.top_frame.pack(fill="x", padx=5, pady=3)
        self.class_label = tk.Label(self.top_frame, text="", fg="#00d4ff", bg="#0a0f1c", font=self.font_class, anchor="w")
        self.class_label.pack(side="left", padx=5)
        
        # 小窗口隐藏管理按钮，只留⚙
        self.admin_btn_frame = tk.Frame(self.top_frame, bg="#0a0f1c")
        self.admin_btn_frame.pack(side="right", padx=5)
        self.btn_new = tk.Button(self.admin_btn_frame, text="+ 新建", bg="#2ecc71", fg="white", font=("微软雅黑",9,"bold"), command=self.add_class, padx=5, pady=2)
        self.btn_del = tk.Button(self.admin_btn_frame, text="- 删除", bg="#e74c3c", fg="white", font=("微软雅黑",9,"bold"), command=self.del_class, padx=5, pady=2)
        self.btn_edit = tk.Button(self.admin_btn_frame, text="✎ 编辑", bg="#f39c12", fg="white", font=("微软雅黑",9,"bold"), command=self.edit_names, padx=5, pady=2)
        self.btn_new.pack(side="left", padx=2)
        self.btn_del.pack(side="left", padx=2)
        self.btn_edit.pack(side="left", padx=2)
        
        self.gear_btn = tk.Button(self.top_frame, text="⚙", bg="#0a0f1c", fg="#888", font=("微软雅黑",14), bd=0, command=self.toggle_admin)
        self.gear_btn.pack(side="right", padx=2)

        # 中部名字
        self.mid_frame = tk.Frame(self.root, bg="#0a0f1c")
        self.mid_frame.pack(expand=True, fill="both", padx=10, pady=5)
        self.name_label = tk.Label(self.mid_frame, text="点击开始", fg="#ffd700", bg="#0a0f1c", font=self.font_name)
        self.name_label.pack(expand=True)
        
        self.remain_label = tk.Label(self.root, text="剩余 0/0", fg="#aaaaaa", bg="#0a0f1c", font=("微软雅黑", 12))
        self.remain_label.pack(pady=2)

        # 底部
        self.bottom_frame = tk.Frame(self.root, bg="#0a0f1c")
        self.bottom_frame.pack(fill="x", padx=5, pady=3)
        self.start_btn = tk.Button(self.bottom_frame, text="开始/停止", bg="#3498db", fg="white", font=self.font_btn, command=self.toggle_roll, padx=10, pady=4)
        self.reset_btn = tk.Button(self.bottom_frame, text="重置", bg="#f39c12", fg="white", font=self.font_btn, command=self.reset_remaining, padx=10, pady=4)
        self.switch_btn = tk.Button(self.bottom_frame, text="换班(Esc)", bg="#27ae60", fg="white", font=self.font_btn, command=self.switch_class, padx=10, pady=4)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=2)
        self.switch_btn.pack(side="left", expand=True, fill="x", padx=2)

        # 悬停显示管理
        self.top_frame.bind("<Enter>", self.show_admin)
        self.top_frame.bind("<Leave>", self.hide_admin)
        self.admin_visible = True
        self.on_resize()

    def toggle_admin(self):
        if self.admin_visible:
            self.admin_btn_frame.pack_forget()
            self.admin_visible = False
        else:
            self.admin_btn_frame.pack(side="right", padx=5)
            self.admin_visible = True

    def show_admin(self, e=None):
        if self.root.winfo_width() < 650:
            self.admin_btn_frame.pack(side="right", padx=5)
    def hide_admin(self, e=None):
        if self.root.winfo_width() < 650:
            self.admin_btn_frame.pack_forget()

    def on_resize(self, e=None):
        w = self.root.winfo_width()
        if w < 650:
            self.admin_btn_frame.pack_forget()
            self.gear_btn.pack(side="right", padx=2)
            self.name_label.config(font=("STXingkai", 55, "bold"))
            self.class_label.config(font=("STXingkai", 22, "bold"))
        else:
            self.admin_btn_frame.pack(side="right", padx=5)
            self.gear_btn.pack_forget()
            self.name_label.config(font=self.font_name)
            self.class_label.config(font=self.font_class)

    def on_click_root(self, e):
        self.wake_up()
        # 排除点击到底部按钮/顶部控件
        if e.y > self.bottom_frame.winfo_y(): return
        if e.y < self.top_frame.winfo_height(): return
        self.toggle_roll()

    def update_class_ui(self):
        cls = self.classes[self.current_idx] if self.classes else ""
        self.class_label.config(text=cls)
        self.name_label.config(fg="#ffd700")
        self.remain_label.config(text=f"剩余 {len(self.remaining)}/{len(self.data.get(cls, []))}")

    def toggle_roll(self, e=None):
        self.wake_up()
        if not self.remaining:
            self.reset_remaining()
            return
        if self.running:
            self.stop_roll()
        else:
            self.running = True
            self.start_time = time.time()
            self.roll_colors = ["#ffd700","#ff4d4d","#4dff88","#4dabff","#bf4dff","#ff8c4d","#4dffff","#ff4dc4"]
            self._roll_step()

    def _roll_step(self):
        if not self.running: return
        t = time.time() - self.start_time
        if t > 3:
            self.stop_roll()
            return
        # 前快后慢
        delay = 60 if t < 2 else 120
        name = random.choice(self.remaining)
        color = self.roll_colors[int(t*10) % len(self.roll_colors)]
        self.name_label.config(text=name, fg=color)
        self.root.after(delay, self._roll_step)

    def stop_roll(self):
        self.running = False
        if self.remaining:
            name = random.choice(self.remaining)
            self.remaining.remove(name)
            self.name_label.config(text=name, fg="#ffd700", font=self.name_label.cget("font"))
        self.update_class_ui()

    def reset_remaining(self):
        cls = self.classes[self.current_idx]
        self.remaining = self.data.get(cls, [])[:]
        self.name_label.config(text="点击开始", fg="#ffd700")
        self.update_class_ui()

    def switch_class(self, e=None):
        self.wake_up()
        if not self.classes: return
        self.current_idx = (self.current_idx + 1) % len(self.classes)
        self.reset_remaining()

    def add_class(self):
        top = tk.Toplevel(self.root)
        top.title("新建班级")
        top.geometry("250x120")
        tk.Label(top, text="班级名称:").pack(padx=10, pady=5)
        ent = tk.Entry(top)
        ent.pack(padx=10)
        ent.focus()
        def ok():
            n = ent.get().strip()
            if n and n not in self.data:
                self.data[n] = []
                self.classes.append(n)
                self.save_data()
                self.current_idx = len(self.classes)-1
                self.reset_remaining()
            top.destroy()
        tk.Button(top, text="确定", command=ok).pack(pady=10)
        top.bind("<Return>", lambda e: ok())

    def del_class(self):
        if len(self.classes) <= 1: return
        cls = self.classes[self.current_idx]
        del self.data[cls]
        self.classes.remove(cls)
        self.current_idx = 0
        self.save_data()
        self.reset_remaining()

    def edit_names(self):
        cls = self.classes[self.current_idx]
        top = tk.Toplevel(self.root)
        top.title(f"编辑名单 - {cls}")
        top.geometry("350x450")
        tk.Label(top, text="每行一个名字:").pack(padx=10, pady=5)
        txt = tk.Text(top, font=("微软雅黑", 12))
        txt.pack(expand=True, fill="both", padx=10, pady=5)
        txt.insert("1.0", "\n".join(self.data[cls]))
        txt.focus()
        
        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=5)
        def save():
            self.data[cls] = [l.strip() for l in txt.get("1.0", "end").splitlines() if l.strip()]
            self.save_data()
            self.reset_remaining()
            top.destroy()
        tk.Button(btn_frame, text="保存 (回车)", bg="#27ae60", fg="white", command=save).pack(side="left", expand=True, padx=5)
        tk.Button(btn_frame, text="取消", command=top.destroy).pack(side="left", expand=True, padx=5)
        top.bind("<Control-Return>", lambda e: save())
        top.bind("<Return>", lambda e: save())

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
