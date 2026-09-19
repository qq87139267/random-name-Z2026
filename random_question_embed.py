import tkinter as tk
import random
import os

class App:
    def __init__(self, root):
        self.root = root
        root.title("💪下一位～～就你啦～～～👉")
        root.attributes('-fullscreen', True)
        root.configure(bg="#1a1a2e")

        # 1. 班级与名单管理（内置保底，防止txt缺失闪退）
        self.classes = {}
        self.load_classes()
        self.class_keys = list(self.classes.keys())
        self.current_idx = 0

        # 初始状态
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class].copy()
        self.remaining_names = self.original_names.copy()

        self.is_rolling = False
        self.timer = None
        self.last_picked = None  # 新增：记录定格的名字

        self.setup_ui()
        self.bind_events()
        self.update_display()

    def load_classes(self):
        """读取txt，若缺失则用默认名单保证不闪退"""
        # 426班
        if os.path.exists("class426.txt"):
            with open("class426.txt", "r", encoding="utf-8") as f:
                self.classes["426班"] = [l.strip() for l in f if l.strip()]
        else:
            self.classes["426班"] = ["默认甲", "默认乙", "默认丙", "默认丁"]

        # 428班
        if os.path.exists("class428.txt"):
            with open("class428.txt", "r", encoding="utf-8") as f:
                self.classes["428班"] = [l.strip() for l in f if l.strip()]
        else:
            self.classes["428班"] = ["备用1", "备用2", "备用3", "备用4"]

        # 若有427班
        if os.path.exists("class427.txt"):
            with open("class427.txt", "r", encoding="utf-8") as f:
                self.classes["427班"] = [l.strip() for l in f if l.strip()]

        # 若都没有，保底
        if not self.classes:
            self.classes["默认班"] = ["李四", "张三", "王五", "赵六"]

    def setup_ui(self):
        self.label_class = tk.Label(
            self.root, text="", font=("微软雅黑", 40, "bold"),
            fg="#4fc3f7", bg="#1a1a2e"
        )
        self.label_class.pack(pady=20)

        self.label_name = tk.Label(
            self.root, text="准备", font=("华文行楷", 120, "bold"),
            fg="#ffeb3b", bg="#1a1a2e"
        )
        self.label_name.pack(expand=True)

        self.label_remain = tk.Label(
            self.root, text="", font=("微软雅黑", 30),
            fg="white", bg="#1a1a2e"
        )
        self.label_remain.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, text="开始/停止", command=self.toggle_roll,
            font=("微软雅黑", 20), width=10, bg="#1e90ff", fg="white"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="重置", command=self.reset,
            font=("微软雅黑", 20), width=10, bg="#ff9800", fg="white"
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

        # 核心修复：只有没定格名字时才显示提示语
        if not self.is_rolling and not self.last_picked:
            if len(self.remaining_names) > 0:
                self.label_name.config(text="按空格")
            else:
                self.label_name.config(text="已抽完")

    def toggle_roll(self):
        if len(self.remaining_names) == 0:
            return

        if self.is_rolling:
            # 停止滚动，定格结果
            self.root.after_cancel(self.timer)
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final  # 记录定格名字
            self.label_name.config(text=final)
            self.is_rolling = False
        else:
            # 开始滚动
            self.last_picked = None  # 清除定格记录
            self.is_rolling = True
            self.roll_tick()

        self.update_display()

    def roll_tick(self):
        if self.is_rolling:
            self.label_name.config(text=random.choice(self.remaining_names))
            self.timer = self.root.after(80, self.roll_tick)

    def switch_class(self):
        """换班：重置所有状态"""
        self.current_idx = (self.current_idx + 1) % len(self.class_keys)
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class].copy()
        self.remaining_names = self.original_names.copy()
        self.is_rolling = False
        self.last_picked = None  # 清除定格
        if self.timer:
            self.root.after_cancel(self.timer)
        self.label_name.config(text="已换班")
        self.update_display()

    def reset(self):
        self.remaining_names = self.original_names.copy()
        self.is_rolling = False
        self.last_picked = None  # 清除定格
        if self.timer:
            self.root.after_cancel(self.timer)
        self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
