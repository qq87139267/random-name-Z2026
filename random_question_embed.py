import tkinter as tk
from tkinter import font
import random
import os
import time

CLASS_FILES = ["class426.txt", "class428.txt"]
IDLE_ALPHA = 0.5
NORMAL_ALPHA = 1.0
IDLE_TIME = 20.0

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("课堂随机点名")
        self.root.geometry("900x600")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", NORMAL_ALPHA)
        self.root.bind("<Escape>", lambda e: self._switch_class())
        self.root.bind("<Button-1>", lambda e: self._reset_alpha())
        self.root.bind("<space>", lambda e: self._draw_name())

        self.current_class_idx = 0
        self.names_pool = []
        self.all_names = []
        self.last_interact = time.time()

        self._load_font()
        self._build_ui()
        self._switch_class(force=0)
        self._ensure_topmost()
        self._tick()

    def _load_font(self):
        self.font_name = "华文行草"
        try:
            if os.path.exists("STXINGKA.TTF"):
                font.Font(root=self.root, family=self.font_name, size=120)
        except Exception:
            self.font_name = "楷体"

    def _build_ui(self):
        self.class_label = tk.Label(self.root, text="", font=(self.font_name, 48), fg="#d32f2f")
        self.class_label.pack(pady=30)
        self.name_label = tk.Label(self.root, text="准备", font=(self.font_name, 140), fg="#1976d2")
        self.name_label.pack(expand=True)
        self.hint = tk.Label(self.root, text="空格抽名 | Esc换班 | 点击恢复", font=("微软雅黑", 16))
        self.hint.pack(pady=20)

    def _read_names(self, path):
        if not os.path.exists(path):
            return ["示例"]
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]

    def _switch_class(self, force=None):
        if force is not None:
            self.current_class_idx = force
        else:
            self.current_class_idx = (self.current_class_idx + 1) % len(CLASS_FILES)
        idx = self.current_class_idx
        self.all_names = self._read_names(CLASS_FILES[idx])
        self.names_pool = self.all_names[:]
        random.shuffle(self.names_pool)
        self.class_label.config(text=CLASS_FILES[idx].replace("class", "").replace(".txt", "") + "班")
        self.name_label.config(text="准备")
        self._reset()
        self._ensure_topmost()

    def _draw_name(self):
        if not self.names_pool:
            self.names_pool = self.all_names[:]
            random.shuffle(self.names_pool)
        name = self.names_pool.pop()
        self.name_label.config(text=name)
        self._reset()

    def _reset(self):
        self.last_interact = time.time()
        self._reset_alpha()
        self._ensure_topmost()

    def _reset_alpha(self):
        self.root.attributes("-alpha", NORMAL_ALPHA)
        self.last_interact = time.time()

    def _ensure_topmost(self):
        self.root.attributes("-topmost", False)
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()

    def _tick(self):
        if time.time() - self.last_interact > IDLE_TIME:
            self.root.attributes("-alpha", IDLE_ALPHA)
        self._ensure_topmost()
        self.root.after(1000, self._tick)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()