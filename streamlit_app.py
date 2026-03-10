"""
Streamlit Cloud 入口文件（必须在根目录）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接运行主应用
exec(open(os.path.join(os.path.dirname(__file__), "ui", "app.py")).read())
