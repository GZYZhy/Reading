#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序 - 主入口
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有必要的模块都已正确安装")
    sys.exit(1)

def main():
    """主函数"""
    try:
        # 创建并运行主窗口
        app = MainWindow()
        app.run()
    except Exception as e:
        # 错误处理
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("错误", f"程序运行时发生错误:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 