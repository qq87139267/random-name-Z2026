import tkinter as tk
import random
import os

class App:
    def __init__(self, root):
        self.root = root
        root.title("💪下一位～～就你啦～～～👉")
        root.geometry("300x200")
        root.configure(bg="#1a1a2e")

        self.classes = {}
        self.class_keys = []
        self.current_idx = 0
        self.current_class = ""
        self.original_names = []
        self.remaining_names = []
        
        self.is_rolling = False
        self.timer = None
        self.last_picked = None
        
        # 自动停止参数
        self.start_time = 0
        self.auto_stop_ms = 3000   # 3秒停
        self.slow_start_ms = 2000  # 2秒后开始减速

        self.load_classes()
        if self.class_keys:
            self.current_class = self.class_keys[0]
            self.original_names = self.classes[self.current_class].copy()
            self.remaining_names = self.original_names.copy()

        self.build_ui()
        self.update_display()
        self.bind_events()

    def load_classes(self):
        # 自动读班级文件（同目录）
        files = {
            "426班": "class426.txt",
            "427班": "class427.txt",
            "428班": "class428.txt",
        }
        for name, f in files.items():
            if os.path.exists(f):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        names = [l.strip() for l in fp if l.strip()]
                        if names:
                            self.classes[name] = names
                except:
                    pass
        self.class_keys = list(self.classes.keys())

    def build_ui(self):
        tk.Label(
            self.root, textvariable=None, text=self.current_class,
            font=("微软雅黑", 40, "bold"), fg="#4cc9f0", bg="#1a1a2e"
        ).pack(pady=(30, 5))
        self.label_class = tk.Label(
            self.root, text="", font=("微软雅黑", 40, "bold"),
            fg="#4cc9f0", bg="#1a1a2e"
        )
        self.label_class.pack(pady=(30, 5))

        self.label_name = tk.Label(
            self.root, text="按空格", font=("楷体", 120, "bold"),
            fg="#f72585", bg="#1a1a2e"
        )
        self.label_name.pack(pady=20)

        self.label_remain = tk.Label(
            self.root, text="", font=("微软雅黑", 30),
            fg="white", bg="#1a1a2e"
        )
        self.label_remain.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=30)

        tk.Button(
            btn_frame, text="开始/停止", command=self.toggle_roll,
            font=("微软雅黑", 20), width=10, bg="#4361ee", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="重置", command=self.reset,
            font=("微软雅黑", 20), width=10, bg="#f8961e", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="换班", command=self.switch_class,
            font=("微软雅黑", 20), width=10, bg="#4caf50", fg="white"
        ).pack(side=tk.LEFT, padx=10)

    def bind_events(self):
        self.root.bind("<space>", lambda e: self.toggle_roll())
        self.root.bind("<Escape>", lambda e: self.switch_class())
        self.root.bind("<Double-1>", lambda e: self.root.attributes('-fullscreen', False))

    def update_display(self):
        self.label_class.config(text=self.current_class)
        self.label_remain.config(text=f"剩余 {len(self.remaining_names)}/{len(self.original_names)}")

        if not self.is_rolling and not self.last_picked:
            if len(self.remaining_names) > 0:
                self.label_name.config(text="按空格")
            else:
                self.label_name.config(text="已抽完")

    def toggle_roll(self):
        if len(self.remaining_names) == 0:
            return

        if self.is_rolling:
            # 手动停止（定格）
            self.root.after_cancel(self.timer)
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final
            self.label_name.config(text=final)
            self.is_rolling = False
        else:
            # 开始滚动（含自动停止+减速）
            self.last_picked = None
            self.is_rolling = True
            self.start_time = self.root.tk.call('clock', 'milliseconds')
            self.roll_tick()
            
            # 3秒后自动停止
            self.root.after(self.auto_stop_ms, self.auto_stop)

        self.update_display()

    def roll_tick(self):
        if not self.is_rolling:
            return
            
        now = self.root.tk.call('clock', 'milliseconds')
        elapsed = now - self.start_time
        
        # 显示滚动名字
        self.label_name.config(text=random.choice(self.remaining_names))
        
        # 计算间隔：前2秒80ms，2~3秒逐渐变慢（80~300ms）
        if elapsed < self.slow_start_ms:
            delay = 80
        else:
            # 减速比例（0~1）
            slow_ratio = min((elapsed - self.slow_start_ms) / (self.auto_stop_ms - self.slow_start_ms), 1)
            delay = int(80 + slow_ratio * 220)  # 80 → 300
            
        self.timer = self.root.after(delay, self.roll_tick)

    def auto_stop(self):
        if self.is_rolling:
            # 最终定格
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final
            self.label_name.config(text=final)
            self.is_rolling = False
            self.update_display()

    def switch_class(self):
        if not self.class_keys:
            return
        self.current_idx = (self.current_idx + 1) % len(self.class_keys)
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class].copy()
        self.remaining_names = self.original_names.copy()
        self.is_rolling = False
        self.last_picked = None
        if self.timer:
            self.root.after_cancel(self.timer)
        self.label_name.config(text="已换班")
        self.update_display()

    def reset(self):
        self.remaining_names = self.original_names.copy()
        self.is_rolling = False
        self.last_picked = None
        if self.timer:
            self.root.after_cancel(self.timer)
        self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
