#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序启动脚本
"""

import sys
import os

def check_dependencies():
    """检查依赖是否已安装"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import configparser
    except ImportError:
        missing_deps.append("configparser")
    
    if missing_deps:
        print("缺少以下依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("锐读 - 速读训练 v1.0")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖...")
    if not check_dependencies():
        sys.exit(1)
    
    print("依赖检查通过！")
    
    # 检查项目结构
    required_dirs = ['core', 'gui', 'sample_articles']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"缺少必要目录: {', '.join(missing_dirs)}")
        sys.exit(1)
    
    print("项目结构检查通过！")
    print("启动程序...")
    
    # 导入并运行主程序
    try:
        from main import main as run_main
        run_main()
    except Exception as e:
        print(f"程序运行时出错: {e}")
        print("请检查错误信息并重试")
        sys.exit(1)

if __name__ == "__main__":
    main() 