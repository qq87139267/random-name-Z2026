# -*- coding: utf-8 -*-
"""
随机点名 · 软件版
功能：
  - 自由新建/删除/切换班级，名单可视化编辑
  - 行草字体（华文行楷 → 楷体 → 隶书 → 雅黑 自动降级）
  - 万花筒彩色滚动 → 金色 3D 定格
  - 3 秒自动停（前 2 秒快滚 + 后 1 秒减速）
  - 20 秒无操作 → 80% 透明，点击任意处恢复
  - 小窗口时顶部管理按钮自动隐藏（鼠标移到顶部才显示）
  - Windows 系统级强制置顶
  - 数据存 rollcall_data.json，关掉再开还在
"""
import json
import os
import random
import time
import tkinter as tk
from tkinter import font as tkfont

try:
    import ctypes
    from ctypes import windll
    HAS_WIN32 = True
except Exception:
    HAS_WIN32 = False

DATA_FILE = "rollcall_data.json"
IDLE_LIMIT = 20          # 20 秒无操作
TRANS_ALPHA = 0.2        # 80% 透明（仅 20% 可见）
NORMAL_ALPHA = 1.0

DEFAULT_DATA = {
    "426班": ["张三", "李四", "王五"],
    "427班": ["赵六", "钱七", "孙八"],
    "428班": ["周九", "吴十", "郑十一"],
}

# 滚动时的万花筒色
KALEIDO = ["#ffd700", "#ff6b6b", "#4ecdc4", "#a29bfe",
           "#fd79a8", "#ffeaa7", "#55efc4", "#ff9ff3",
           "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd"]


class RollCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("下一位~~就係你~~~")
        self.root.geometry("900x680")
        self.root.minsize(480, 400)
        self.root.configure(bg="#1a1a2e")

        self.data = self.load_data()
        self.classes = list(self.data.keys())
        self.current_idx = 0
        self.remaining = []
        self.running = False
        self.timer = None
        self.roll_start = 0
        self.last_active = time.time()

        # 行草字体：Tk 会自动选第一个已安装的
        self.title_family = self._pick_font(
            ["STXingkai", "华文行楷", "Xingkai SC", "KaiTi", "KaiTi_GB2312", "LiSu"]
        )
        self.btn_family = self._pick_font(["Microsoft YaHei", "微软雅黑"])

        self._build_ui()
        self._reset_remaining()
        self._make_topmost()
        self._bind_events()
        self._refresh_all()
        self.tick()

    # ---------------- 字体 / 数据 ----------------
    def _pick_font(self, candidates):
        available = {name.lower() for name in tkfont.families()}
        for c in candidates:
            if c.lower() in available:
                return c
        return candidates[-1]

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict) and d:
                    return d
            except Exception:
                pass
        return {k: list(v) for k, v in DEFAULT_DATA.items()}

    def save_data(self):
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)

    # ---------------- 界面 ----------------
    def _build_ui(self):
        # 顶部：班级标题 + 管理按钮
        self.top = tk.Frame(self.root, bg="#1a1a2e")
        self.top.pack(fill="x", padx=14, pady=(14, 6))

        self.class_label = tk.Label(
            self.top, text="", fg="#00d4ff", bg="#1a1a2e"
        )
        self.class_label.pack(side="left", padx=4)

        self.admin = tk.Frame(self.top, bg="#1a1a2e")
        self.admin.pack(side="right")

        tk.Button(self.admin, text="+ 新建班级", bg="#27ae60", fg="white",
                  font=(self.btn_family, 12), command=self.add_class,
                  cursor="hand2").pack(side="left", padx=3)
        tk.Button(self.admin, text="- 删除当前班", bg="#e74c3c", fg="white",
                  font=(self.btn_family, 12), command=self.del_class,
                  cursor="hand2").pack(side="left", padx=3)
        tk.Button(self.admin, text="✎ 编辑名单", bg="#e67e22", fg="white",
                  font=(self.btn_family, 12), command=self.edit_names,
                  cursor="hand2").pack(side="left", padx=3)

        # 中间：名字（点击可开始/停止）
        self.mid = tk.Frame(self.root, bg="#1a1a2e")
        self.mid.pack(expand=True, fill="both")

        self.name_label = tk.Label(
            self.mid, text="点击开始", fg="#ffd700", bg="#1a1a2e",
            cursor="hand2",
        )
        self.name_label.pack(expand=True)
        self.name_label.bind("<Button-1>", lambda e: self.toggle_start())

        self.remain_label = tk.Label(
            self.mid, text="", fg="#cccccc", bg="#1a1a2e",
            font=(self.btn_family, 16),
        )
        self.remain_label.pack(pady=10)

        # 底部：核心按钮
        self.bot = tk.Frame(self.root, bg="#1a1a2e")
        self.bot.pack(fill="x", padx=14, pady=(6, 14))

        self.start_btn = tk.Button(
            self.bot, text="开始 / 停止 (空格)", bg="#3498db", fg="white",
            font=(self.btn_family, 14), cursor="hand2",
            command=self.toggle_start,
        )
        self.reset_btn = tk.Button(
            self.bot, text="重置", bg="#e67e22", fg="white",
            font=(self.btn_family, 14), cursor="hand2", command=self._reset_remaining,
        )
        self.switch_btn = tk.Button(
            self.bot, text="换班 (Esc)", bg="#27ae60", fg="white",
            font=(self.btn_family, 14), cursor="hand2", command=self.switch_class,
        )
        for b in (self.start_btn, self.reset_btn, self.switch_btn):
            b.pack(side="left", expand=True, fill="x", padx=5, ipady=6)

    # ---------------- 置顶 / 自适应 ----------------
    def _make_topmost(self):
        if not HAS_WIN32:
            self.root.wm_attributes("-topmost", True)
            return
        try:
            self.root.wm_attributes("-topmost", True)
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_SHOWWINDOW = 0x0040
            SWP_NOACTIVATE = 0x0010
            windll.user32.SetWindowPos(
                hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0,
                SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW | SWP_NOACTIVATE,
            )
        except Exception:
            pass

    def _bind_events(self):
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<space>", lambda e: self.toggle_start())
        self.root.bind("<Escape>", lambda e: self.switch_class())
        # 唤醒透明
        self.root.bind("<Motion>", self.wake_up)
        self.root.bind("<Key>", self.wake_up)
        self.root.bind("<Button-1>", self.wake_up)
        # 顶部悬停显隐管理按钮
        self.top.bind("<Enter>", self._show_admin)
        self.top.bind("<Leave>", self._hide_admin)

    def _on_resize(self, event=None):
        # 只响应根窗口自身尺寸变化
        if event is not None and event.widget is not self.root:
            return
        w = self.root.winfo_width()
        if w < 650:
            # 小窗口：管理按钮隐藏、字号缩小、按钮紧凑
            self.class_label.config(font=(self.title_family, 32))
            self.name_label.config(font=(self.title_family, 84))
            for b in (self.start_btn, self.reset_btn, self.switch_btn):
                b.config(font=(self.btn_family, 12), padx=4, ipady=4)
            self._hide_admin()
        else:
            self.class_label.config(font=(self.title_family, 46))
            self.name_label.config(font=(self.title_family, 130))
            for b in (self.start_btn, self.reset_btn, self.switch_btn):
                b.config(font=(self.btn_family, 14), padx=10, ipady=6)
            self.admin.pack(side="right")

    def _show_admin(self, event=None):
        if self.root.winfo_width() < 650:
            self.admin.pack(side="right")

    def _hide_admin(self, event=None):
        if self.root.winfo_width() < 650:
            self.admin.pack_forget()

    # ---------------- 数据/显示 ----------------
    def _current(self):
        return self.classes[self.current_idx]

    def _refresh_all(self):
        cls = self._current()
        self.class_label.config(text=cls)
        self.remain_label.config(
            text="剩余 {}/{}".format(len(self.remaining), len(self.data.get(cls, [])))
        )

    def _set_gold(self, text):
        """金色定格"""
        self.name_label.config(text=text, fg="#FFD700")

    def _reset_remaining(self):
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.running = False
        self.remaining = list(self.data.get(self._current(), []))
        self._set_gold("点击开始")
        self._refresh_all()

    # ---------------- 抽名逻辑 ----------------
    def toggle_start(self):
        self.wake_up()
        if self.running:
            self._stop_roll()
            return
        if not self.remaining:
            self._reset_remaining()
            return
        self.running = True
        self.roll_start = time.time()
        self.name_label.config(fg="#ff4081")
        self._roll_tick()

    def _roll_tick(self):
        if not self.running:
            return
        elapsed = (time.time() - self.roll_start) * 1000
        name = random.choice(self.remaining)
        self.name_label.config(text=name, fg=random.choice(KALEIDO))

        if elapsed < 2000:
            delay = 60
        else:
            ratio = min((elapsed - 2000) / 1000.0, 1.0)
            delay = int(60 + ratio * 240)
        self.timer = self.root.after(delay, self._roll_tick)

        # 3 秒自动停
        if elapsed >= 3000:
            self._stop_roll()

    def _stop_roll(self):
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None
        if not self.running:
            return
        self.running = False
        final = random.choice(self.remaining)
        self.remaining.remove(final)
        self._set_gold(final)
        self._refresh_all()

    def switch_class(self):
        self.wake_up()
        if not self.classes:
            return
        self.current_idx = (self.current_idx + 1) % len(self.classes)
        self._reset_remaining()

    # ---------------- 班级管理 ----------------
    def add_class(self):
        self._popup_name("新建班级", "班级名称：", "", self._do_add)

    def _do_add(self, name, top):
        name = name.strip()
        if not name:
            top.destroy()
            return
        if name in self.data:
            top.destroy()
            return
        self.data[name] = []
        self.classes = list(self.data.keys())
        self.current_idx = len(self.classes) - 1
        self.save_data()
        self._reset_remaining()
        self._refresh_all()
        top.destroy()
        self.edit_names()  # 新建后直接编辑名单

    def del_class(self):
        if len(self.classes) <= 1:
            return
        cls = self._current()
        if not self._confirm("删除班级", "确定删除「{}」吗？".format(cls)):
            return
        del self.data[cls]
        self.classes = list(self.data.keys())
        self.current_idx = 0
        self.save_data()
        self._reset_remaining()
        self._refresh_all()

    def edit_names(self):
        cls = self._current()
        top = tk.Toplevel(self.root)
        top.title("编辑名单 - {}".format(cls))
        top.geometry("420x460")
        top.transient(self.root)
        top.grab_set()
        tk.Label(top, text="一行一个名字：", font=(self.btn_family, 12)).pack(
            anchor="w", padx=12, pady=(12, 4))

        txt = tk.Text(top, font=(self.btn_family, 14), wrap="none")
        txt.pack(expand=True, fill="both", padx=12)
        txt.insert("1.0", "\n".join(self.data.get(cls, [])))

        def save():
            names = [ln.strip() for ln in txt.get("1.0", "end").splitlines() if ln.strip()]
            self.data[cls] = names
            self.save_data()
            self._reset_remaining()
            self._refresh_all()
            top.destroy()

        tk.Button(top, text="保存", bg="#27ae60", fg="white",
                  font=(self.btn_family, 13), cursor="hand2",
                  command=save).pack(fill="x", padx=12, pady=12)

    def _popup_name(self, title, prompt, default, on_ok):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.transient(self.root)
        top.grab_set()
        tk.Label(top, text=prompt, font=(self.btn_family, 12)).pack(
            padx=14, pady=(14, 4))
        ent = tk.Entry(top, font=(self.btn_family, 14))
        ent.insert(0, default)
        ent.pack(padx=14, fill="x")
        ent.select_range(0, "end")
        ent.focus_set()

        def ok():
            on_ok(ent.get(), top)

        ent.bind("<Return>", lambda e: ok())
        tk.Button(top, text="确定", bg="#3498db", fg="white",
                  font=(self.btn_family, 12), cursor="hand2",
                  command=ok).pack(pady=14)

    def _confirm(self, title, msg):
        box = tk.Toplevel(self.root)
        box.title(title)
        box.transient(self.root)
        box.grab_set()
        result = {"val": False}
        tk.Label(box, text=msg, font=(self.btn_family, 12),
                 wraplength=280, justify="left").pack(padx=16, pady=16)

        def yes():
            result["val"] = True
            box.destroy()

        def no():
            box.destroy()

        btns = tk.Frame(box)
        btns.pack(pady=(0, 14))
        tk.Button(btns, text="确定", bg="#e74c3c", fg="white",
                  font=(self.btn_family, 12), cursor="hand2",
                  command=yes, width=8).pack(side="left", padx=8)
        tk.Button(btns, text="取消", font=(self.btn_family, 12),
                  cursor="hand2", command=no, width=8).pack(side="left", padx=8)
        self.root.wait_window(box)
        return result["val"]

    # ---------------- 透明 / 置顶保活 ----------------
    def wake_up(self, event=None):
        self.last_active = time.time()
        self.root.attributes("-alpha", NORMAL_ALPHA)
        if HAS_WIN32:
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                windll.user32.SetLayeredWindowAttributes(
                    hwnd, 0, int(NORMAL_ALPHA * 255), 2)
            except Exception:
                pass

    def tick(self):
        idle = time.time() - self.last_active
        if idle >= IDLE_LIMIT and not self.running:
            self.root.attributes("-alpha", TRANS_ALPHA)
            if HAS_WIN32:
                try:
                    hwnd = windll.user32.GetParent(self.root.winfo_id())
                    windll.user32.SetLayeredWindowAttributes(
                        hwnd, 0, int(TRANS_ALPHA * 255), 2)
                except Exception:
                    pass
        else:
            self.root.attributes("-alpha", NORMAL_ALPHA)
        self.root.after(500, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    app = RollCallApp(root)
    root.mainloop()
