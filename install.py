#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(c)2025 ZhangWeb GZYZhy
Reading Training - Apache License 2.0

锐读 - 速读训练程序安装脚本
"""

import subprocess
import sys
import os

def install_dependencies():
    """安装依赖包"""
    print("锐读 - 速读训练 - 依赖安装程序")
    print("=" * 50)
    
    if not os.path.exists("requirements.txt"):
        print("错误: 找不到 requirements.txt 文件")
        return False
    
    try:
        print("正在安装依赖包...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        print("依赖安装成功！")
        print("\n安装的包:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"安装过程中出现错误: {e}")
        return False

def verify_installation():
    """验证安装"""
    print("\n验证安装...")
    
    packages_to_check = [
        ("tkinter", "tkinter"),
        ("Pillow", "PIL"),
        ("configparser", "configparser")
    ]
    
    success = True
    for package_name, import_name in packages_to_check:
        try:
            __import__(import_name)
            print(f"✓ {package_name} 已正确安装")
        except ImportError:
            print(f"✗ {package_name} 安装失败或无法导入")
            success = False
    
    return success

def main():
    """主函数"""
    if install_dependencies():
        if verify_installation():
            print("\n" + "=" * 50)
            print("安装完成！现在可以运行程序了:")
            print("python start.py")
            print("或者")
            print("python main.py")
        else:
            print("\n安装验证失败，请检查错误信息")
    else:
        print("\n安装失败，请手动安装依赖")

if __name__ == "__main__":
    main() 