# -*- coding: utf-8 -*-
"""
随机点名 · 桌面软件版（Python + tkinter）
功能：自由管理班级 / 粘贴名单 / 行草字体 / 万花筒滚动 /
      金色3D定格 / 3秒自动停(2快+1减速) / 20秒70%透明 / 点击名字开始
数据保存在同目录 rollcall_data.json，关掉再开还在。
"""
import os
import json
import random
import time
import threading
import tkinter as tk
from tkinter import font as tkfont

# ========== Windows 强制置顶 ==========
try:
    import ctypes
    user32 = ctypes.WinDLL('user32')
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_SHOWWINDOW = 0x0040

    def force_topmost(hwnd):
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        )
except Exception:
    def force_topmost(hwnd):
        pass


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "rollcall_data.json")

# 行草字体优先级（Windows 自带华文行楷 STXingkai，无需额外安装）
CALLIGRAPHY = ["STXingkai", "Xingkai SC", "KaiTi", "LiSu", "Microsoft YaHei"]

# 万花筒 12 色
COLORS = [
    "#ff4081", "#ffeb3b", "#00e5ff", "#76ff03",
    "#e040fb", "#ff6e40", "#18ffff", "#ffff00",
    "#f50057", "#00ffa0", "#651fff", "#ffd740",
]


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("💪 →下一位～～就係你～～～👉↗")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#1a1a2e")

        hwnd = ctypes.c_void_p(self.root.winfo_id()) if 'ctypes' in globals() else None
        try:
            force_topmost(hwnd)
        except Exception:
            self.root.wm_attributes('-topmost', 1)

        # 透明度：70% 透明 = 保留 0.3
        self.alpha_normal = 1.0
        self.alpha_dim = 0.3
        self.idle_seconds = 0
        self.idle_limit = 20

        # 自动停止参数
        self.auto_stop_ms = 3000
        self.slow_start_ms = 2000
        self.timer = None
        self.is_rolling = False
        self.last_picked = None
        self.start_time = 0
        self.color_idx = 0

        # 数据：{ "426班": ["张三", ...], ... }
        self.classes = self.load_data()
        if not self.classes:
            self.classes = {"426班": ["蔡家乐", "吴莹莹", "廖梓良"]}
        self.class_keys = list(self.classes.keys())
        self.current_idx = 0
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class][:]
        self.remaining_names = self.original_names[:]

        self.build_ui()
        self.bind_events()
        self.update_display()
        self.start_idle_timer()

    # -------- 数据持久化 --------
    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.classes, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # -------- 界面 --------
    def build_ui(self):
        # 顶部：班级选择 + 管理按钮
        top = tk.Frame(self.root, bg="#1a1a2e")
        top.pack(pady=(18, 6), fill=tk.X)

        self.label_class = tk.Label(
            top, text="", font=("Microsoft YaHei", 36, "bold"),
            fg="#00d4ff", bg="#1a1a2e"
        )
        self.label_class.pack(side=tk.LEFT, padx=20)

        tk.Button(top, text="＋ 新建班级", command=self.add_class,
                  font=("Microsoft YaHei", 14), bg="#4caf50", fg="white",
                  padx=8).pack(side=tk.LEFT, padx=4)
        tk.Button(top, text="－ 删除当前班", command=self.remove_class,
                  font=("Microsoft YaHei", 14), bg="#f44336", fg="white",
                  padx=8).pack(side=tk.LEFT, padx=4)
        tk.Button(top, text="✎ 编辑名单", command=self.edit_names,
                  font=("Microsoft YaHei", 14), bg="#ff9800", fg="white",
                  padx=8).pack(side=tk.LEFT, padx=4)

        # 名字区域（行草字体）
        center = tk.Frame(self.root, bg="#1a1a2e")
        center.pack(expand=True)
        self.label_name = tk.Label(
            center, text="点击开始",
            font=(CALLIGRAPHY[0], 130, "bold"),
            fg="#FFD700", bg="#1a1a2e", cursor="hand2"
        )
        self.label_name.pack(padx=40)
        self.label_name.bind("<Button-1>", lambda e: self.toggle_roll())

        # 剩余
        bottom = tk.Frame(self.root, bg="#1a1a2e")
        bottom.pack(pady=10)
        self.label_remain = tk.Label(
            bottom, text="", font=("Microsoft YaHei", 24),
            fg="white", bg="#1a1a2e"
        )
        self.label_remain.pack()

        # 底部按钮
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="开始 / 停止", command=self.toggle_roll,
                  font=("Microsoft YaHei", 20), width=12, bg="#2196f3", fg="white"
                  ).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="重置", command=self.reset_class,
                  font=("Microsoft YaHei", 20), width=10, bg="#ff9800", fg="white"
                  ).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="换班 (Esc)", command=self.switch_class,
                  font=("Microsoft YaHei", 20), width=12, bg="#4caf50", fg="white"
                  ).pack(side=tk.LEFT, padx=10)

    def bind_events(self):
        self.root.bind("<space>", lambda e: self.toggle_roll())
        self.root.bind("<Escape>", lambda e: self.switch_class())
        self.root.bind("<Double-1>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Motion>", self.reset_idle)
        self.root.bind("<Key>", self.reset_idle)
        self.root.bind("<Button-1>", self.reset_idle)

    # -------- 班级管理 --------
    def refresh_class(self):
        self.class_keys = list(self.classes.keys())
        if self.current_idx >= len(self.class_keys):
            self.current_idx = 0
        if self.class_keys:
            self.current_class = self.class_keys[self.current_idx]
            self.original_names = self.classes[self.current_class][:]
        else:
            self.current_class = ""
            self.original_names = []
        self.remaining_names = self.original_names[:]
        self.save_data()
        self.update_display()

    def add_class(self):
        self.open_text_dialog(
            "新建班级", "输入新班级名称：", "",
            on_ok=lambda val: self._do_add_class(val)
        )

    def _do_add_class(self, name):
        name = (name or "").strip()
        if not name:
            return
        if name in self.classes:
            self.flash("班级已存在")
            return
        self.classes[name] = []
        self.current_idx = len(self.classes) - 1
        self.is_rolling = False
        self.last_picked = None
        self.refresh_class()
        # 新建后直接打开编辑名单
        self.edit_names()

    def remove_class(self):
        if len(self.class_keys) <= 1:
            self.flash("至少保留一个班级")
            return
        self.open_text_dialog(
            "删除班级",
            f"确定删除班级「{self.current_class}」？\n\n输入 yes 确认：",
            "",
            on_ok=lambda val: self._do_remove(val)
        )

    def _do_remove(self, val):
        if (val or "").strip().lower() != "yes":
            return
        del self.classes[self.current_class]
        self.current_idx = 0
        self.is_rolling = False
        self.last_picked = None
        self.refresh_class()

    def edit_names(self):
        current = "\n".join(self.classes.get(self.current_class, []))
        self.open_text_dialog(
            f"编辑名单 - {self.current_class}",
            "每行一个名字：",
            current,
            big=True,
            on_ok=lambda val: self._do_save_names(val)
        )

    def _do_save_names(self, text):
        names = [n.strip() for n in (text or "").split("\n") if n.strip()]
        self.classes[self.current_class] = names
        self.is_rolling = False
        self.last_picked = None
        self.refresh_class()
        self.flash(f"已保存 {len(names)} 人")

    # -------- 通用弹窗 --------
    def open_text_dialog(self, title, prompt, default, on_ok, big=False):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.grab_set()
        win.configure(bg="#1a1a2e")
        try:
            force_topmost(ctypes.c_void_p(win.winfo_id()))
        except Exception:
            pass
        tk.Label(win, text=prompt, font=("Microsoft YaHei", 13),
                 fg="white", bg="#1a1a2e", justify=tk.LEFT).pack(padx=15, pady=10)

        if big:
            widget = tk.Text(win, font=("Microsoft YaHei", 14),
                             width=30, height=14, wrap=tk.WORD)
        else:
            widget = tk.Entry(win, font=("Microsoft YaHei", 14), width=30)
        widget.pack(padx=15, pady=5)
        widget.insert("1.0" if big else 0, default)

        def submit():
            val = widget.get("1.0", tk.END).strip() if big else widget.get().strip()
            win.destroy()
            on_ok(val)

        tk.Button(win, text="确定", command=submit,
                  font=("Microsoft YaHei", 13), bg="#2196f3", fg="white",
                  width=10).pack(pady=12)
        widget.focus_set()

    def flash(self, msg):
        self.label_name.config(text=msg, fg="#FFD700")
        self.last_picked = None
        self.update_display()

    # -------- 显示 --------
    def _set_gold_3d(self, text):
        self.label_name.config(
            text=text, fg="#FFD700", bg="#1a1a2e",
            font=(CALLIGRAPHY[0], 140, "bold"),
            relief="ridge", borderwidth=6, highlightthickness=0,
        )

    def _clear_3d(self):
        self.label_name.config(relief="flat", borderwidth=0)

    def update_display(self):
        self.label_class.config(text=self.current_class)
        self.label_remain.config(
            text=f"剩余 {len(self.remaining_names)}/{len(self.original_names)}"
        )
        if not self.is_rolling and not self.last_picked:
            self._clear_3d()
            self.label_name.config(font=(CALLIGRAPHY[0], 130, "bold"))
            if len(self.remaining_names) > 0:
                self.label_name.config(text="点击开始", fg="#FFD700")
            else:
                self.label_name.config(text="已抽完", fg="#FFD700")

    # -------- 滚动 / 停止 --------
    def toggle_roll(self):
        if len(self.remaining_names) == 0:
            self.flash("名单为空，请编辑名单")
            return
        if self.is_rolling:
            self.stop_roll()
        else:
            self.start_roll()

    def start_roll(self):
        self.last_picked = None
        self._clear_3d()
        self.label_name.config(font=(CALLIGRAPHY[0], 130, "bold"))
        self.is_rolling = True
        self.start_time = self.root.tk.call('clock', 'milliseconds')
        self.color_idx = 0
        self.roll_tick()
        self.root.after(self.auto_stop_ms, self.stop_roll)
        self.update_display()

    def roll_tick(self):
        if not self.is_rolling:
            return
        now = self.root.tk.call('clock', 'milliseconds')
        elapsed = now - self.start_time

        color = COLORS[self.color_idx % len(COLORS)]
        self.color_idx += 1
        self.label_name.config(
            text=random.choice(self.remaining_names),
            fg=color, bg="#1a1a2e",
            font=(CALLIGRAPHY[0], 130, "bold"),
        )

        if elapsed < self.slow_start_ms:
            delay = 80
        else:
            ratio = min((elapsed - self.slow_start_ms) /
                        (self.auto_stop_ms - self.slow_start_ms), 1)
            delay = int(80 + ratio * 220)
        self.timer = self.root.after(delay, self.roll_tick)

    def stop_roll(self):
        if not self.is_rolling and self.last_picked:
            return
        self.is_rolling = False
        if self.timer:
            try:
                self.root.after_cancel(self.timer)
            except Exception:
                pass
        if self.remaining_names:
            final = random.choice(self.remaining_names)
            self.remaining_names.remove(final)
            self.last_picked = final
            self._set_gold_3d(final)
        else:
            self.last_picked = None
            self._clear_3d()
            self.label_name.config(text="已抽完", fg="#FFD700")
        self.update_display()

    def switch_class(self):
        if not self.class_keys:
            return
        if self.timer:
            try:
                self.root.after_cancel(self.timer)
            except Exception:
                pass
        self.current_idx = (self.current_idx + 1) % len(self.class_keys)
        self.current_class = self.class_keys[self.current_idx]
        self.original_names = self.classes[self.current_class][:]
        self.remaining_names = self.original_names[:]
        self.is_rolling = False
        self.last_picked = None
        self.label_class.config(text=self.current_class)
        self._clear_3d()
        self.label_name.config(font=(CALLIGRAPHY[0], 130, "bold"))
        self.label_name.config(text="已换班", fg="#FFD700")
        self.update_display()
        self.root.update_idletasks()
        try:
            force_topmost(ctypes.c_void_p(self.root.winfo_id()))
        except Exception:
            pass

    def reset_class(self):
        self.remaining_names = self.original_names[:]
        self.is_rolling = False
        self.last_picked = None
        if self.timer:
            try:
                self.root.after_cancel(self.timer)
            except Exception:
                pass
        self._clear_3d()
        self.label_name.config(font=(CALLIGRAPHY[0], 130, "bold"))
        self.update_display()

    def toggle_fullscreen(self):
        self.root.attributes('-fullscreen',
                             not self.root.attributes('-fullscreen'))

    # -------- 空闲透明 --------
    def reset_idle(self, event=None):
        self.idle_seconds = 0
        self.root.attributes('-alpha', self.alpha_normal)
        try:
            force_topmost(ctypes.c_void_p(self.root.winfo_id()))
        except Exception:
            pass

    def start_idle_timer(self):
        def tick():
            while True:
                self.root.after(1000, self._tick_idle)
                time.sleep(1)
        threading.Thread(target=tick, daemon=True).start()

    def _tick_idle(self):
        self.idle_seconds += 1
        try:
            force_topmost(ctypes.c_void_p(self.root.winfo_id()))
        except Exception:
            pass
        if self.idle_seconds >= self.idle_limit:
            self.root.attributes('-alpha', self.alpha_dim)


if __name__ == "__main__":
    root = tk.Tk()
    # 尝试加载行草字体（Windows 自带 STXingkai，找不到会自动降级）
    App(root)
    root.mainloop()
