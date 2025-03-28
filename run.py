#!/usr/bin/env python3
import os
import subprocess
import sys

def check_requirements():
    """检查并安装所需的依赖"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        print("安装依赖失败，请检查网络连接或手动安装依赖。")
        return False

def main():
    # 确保在正确的目录中
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查并安装依赖
    print("正在检查依赖...")
    if not check_requirements():
        sys.exit(1)
    
    # 启动 Streamlit 应用
    print("正在启动爬虫工具...")
    try:
        subprocess.run(["streamlit", "run", "src/app.py"], check=True)
    except subprocess.CalledProcessError:
        print("启动失败，请确保已正确安装所有依赖。")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n程序已终止")

if __name__ == "__main__":
    main() 