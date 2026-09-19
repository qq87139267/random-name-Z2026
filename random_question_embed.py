import tkinter as tk
import random
import os
import ctypes
import threading
import time

# ========== Windows 强制置顶 ==========
user32 = ctypes.WinDLL('user32')
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

def force_topmost(hwnd):
    user32.SetWindowPos(
        hwnd, HWND_TOPMOST,
        0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    )

# ========== 主程序 ==========
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("💪下一位～～就你啦～～～👉")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#1a1a2e")

        # 强制置顶（Windows API）
        hwnd = ctypes.c_void_p(self.root.winfo_id())
        force_topmost(hwnd)

        # 透明度控制
        self.alpha_normal = 1.0
        self.alpha_dim = 0.5
        self.idle_seconds = 0
        self.idle_limit = 20  # 10秒无操作变半透明
        self.idle_timer_running = False

        # 自动停止参数
        self.auto_stop_ms = 3000   # 总滚动3秒
        self.slow_start_ms = 2000  # 2秒后减速
        self.timer = None
        self.is_rolling = False
        self.last_picked = None
        self.start_time = 0

        # 读取班级名单
        self.classes = {}
        self.class_keys = []
        for cls in ["426", "427", "428"]:
            fname = f"class{cls}.txt"
            if os.path.exists(fname):
                with open(fname, "r", encoding="utf-8") as f:
                    names = [n.strip() for n in f.readlines() if n.strip()]
                    if names:
                        self.classes[f"{cls}班"] = names
        self.class_keys = list(self.classes.keys())
        if not self.class_keys:
            self.class_keys = ["无名单"]
            self.classes["无名单"] = ["测试"]

        self.current_idx = 0
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class].copy()
        self.remaining_names = self.original_names.copy()

        self.build_ui()
        self.bind_events()
        self.update_display()
        self.start_idle_timer()

    def build_ui(self):
        top = tk.Frame(self.root, bg="#1a1a2e")
        top.pack(pady=20)
        self.label_class = tk.Label(
            top, text="", font=("微软雅黑", 40, "bold"),
            fg="#00d4ff", bg="#1a1a2e"
        )
        self.label_class.pack()

        center = tk.Frame(self.root, bg="#1a1a2e")
        center.pack(expand=True)
        self.label_name = tk.Label(
            center, text="按空格", font=("微软雅黑", 120, "bold"),
            fg="gold", bg="#1a1a2e"
        )
        self.label_name.pack()

        bottom = tk.Frame(self.root, bg="#1a1a2e")
        bottom.pack(pady=20)
        self.label_remain = tk.Label(
            bottom, text="", font=("微软雅黑", 24),
            fg="white", bg="#1a1a2e"
        )
        self.label_remain.pack()

        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=30)

        tk.Button(
            btn_frame, text="开始/停止", command=self.toggle_roll,
            font=("微软雅黑", 20), width=10, bg="#2196f3", fg="white"
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
        self.root.bind("<Motion>", self.reset_idle)
        self.root.bind("<Key>", self.reset_idle)
        self.root.bind("<Button-1>", self.reset_idle)

    def reset_idle(self, event=None):
        self.idle_seconds = 0
        self.root.attributes('-alpha', self.alpha_normal)
        # 唤醒时刷新置顶
        hwnd = ctypes.c_void_p(self.root.winfo_id())
        force_topmost(hwnd)

    def start_idle_timer(self):
        def tick():
            while True:
                self.root.after(1000, self._tick_idle)
                time.sleep(1)
        t = threading.Thread(target=tick, daemon=True)
        t.start()

    def _tick_idle(self):
        self.idle_seconds += 1
        hwnd = ctypes.c_void_p(self.root.winfo_id())
        force_topmost(hwnd)  # 持续保置顶
        if self.idle_seconds >= self.idle_limit:
            self.root.attributes('-alpha', self.alpha_dim)

    def update_display(self):
        self.label_class.config(text=self.current_class)
        self.label_remain.config(
            text=f"剩余 {len(self.remaining_names)}/{len(self.original_names)}"
        )
        if not self.is_rolling and not self.last_picked:
            if len(self.remaining_names) > 0:
                self.label_name.config(text="按空格", fg="gold")
            else:
                self.label_name.config(text="已抽完", fg="gold")

    def toggle_roll(self):
        if len(self.remaining_names) == 0:
            return

        if self.is_rolling:
            self.root.after_cancel(self.timer)
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final
            self.label_name.config(text=final, fg="gold")
            self.is_rolling = False
        else:
            self.last_picked = None
            self.is_rolling = True
            self.start_time = self.root.tk.call('clock', 'milliseconds')
            self.label_name.config(fg="#ff4081")
            self.roll_tick()
            self.root.after(self.auto_stop_ms, self.auto_stop)

        self.update_display()

    def roll_tick(self):
        if not self.is_rolling:
            return
        now = self.root.tk.call('clock', 'milliseconds')
        elapsed = now - self.start_time

        self.label_name.config(
            text=random.choice(self.remaining_names), fg="#ff4081"
        )

        if elapsed < self.slow_start_ms:
            delay = 80
        else:
            ratio = min(
                (elapsed - self.slow_start_ms) /
                (self.auto_stop_ms - self.slow_start_ms), 1
            )
            delay = int(80 + ratio * 220)
        self.timer = self.root.after(delay, self.roll_tick)

    def auto_stop(self):
        if self.is_rolling:
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final
            self.label_name.config(text=final, fg="gold")
            self.is_rolling = False
            self.update_display()

    def switch_class(self):
        if not self.class_keys:
            return
        if self.timer:
            self.root.after_cancel(self.timer)

        self.current_idx = (self.current_idx + 1) % len(self.class_keys)
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class].copy()
        self.remaining_names = self.original_names.copy()

        self.is_rolling = False
        self.last_picked = None

        self.label_class.config(text=self.current_class)
        self.label_name.config(text="已换班", fg="gold")
        self.update_display()
        self.root.update_idletasks()

        # 换班后刷新置顶
        hwnd = ctypes.c_void_p(self.root.winfo_id())
        force_topmost(hwnd)

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
