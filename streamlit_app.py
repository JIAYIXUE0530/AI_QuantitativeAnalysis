"""
Streamlit Cloud 入口
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

st.set_page_config(
    page_title="AI量化投资系统",
    page_icon="https://img.icons8.com/fluency/48/combo-chart.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("ui/pages/1_dashboard.py", title="总览仪表盘"),
    st.Page("ui/pages/2_analysis.py",  title="因子分析"),
    st.Page("ui/pages/3_decision.py",  title="决策中心"),
    st.Page("ui/pages/4_backtest.py",  title="策略回测"),
    st.Page("ui/pages/0_guide.py",     title="使用手册"),
]

pg = st.navigation(pages)
pg.run()
