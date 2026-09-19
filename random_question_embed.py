import tkinter as tk
import random
import os

# 读取名单
def load_names(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

names_426 = load_names('class426.txt')
names_428 = load_names('class428.txt')
current_class = 426
all_names = names_426

# 初始化窗口
root = tk.Tk()
root.title("随机抽名")
root.attributes('-fullscreen', True)
root.bind('<Escape>', lambda e: root.destroy())

# 字体与显示
font_path = 'STXINGKA.TTF'
try:
    root.tk.call('font', 'create', 'myfont', '-family', 'STXingkai', '-size', 120)
    font_name = 'myfont'
except:
    font_name = ('楷体', 120)

label = tk.Label(root, text="按空格抽名\nEsc换班", font=font_name, fg='red')
label.pack(expand=True)

running = False

def toggle_class():
    global current_class, all_names
    current_class = 428 if current_class == 426 else 426
    all_names = names_428 if current_class == 428 else names_426
    label.config(text=f"已切换到 {current_class}班\n按空格抽名")

def roll():
    if running and all_names:
        label.config(text=random.choice(all_names))
        root.after(50, roll)

def on_space(event):
    global running
    if not all_names:
        label.config(text="名单为空")
        return
    if event.keysym == 'space':
        if not running:
            running = True
            roll()
        else:
            running = False
    elif event.keysym == 'Escape':
        toggle_class()

root.bind('<space>', on_space)
root.bind('<Key>', on_space)
root.mainloop()
