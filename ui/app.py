"""
AI量化投资系统 - Streamlit 主入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.components.override_manager import (
    load_weights, load_score_overrides, load_decision_overrides
)
from ui.style import THINKCELL_CSS

st.set_page_config(
    page_title="AI量化投资系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(THINKCELL_CSS, unsafe_allow_html=True)

# ── Session State 初始化 ──
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None

if "custom_weights" not in st.session_state:
    st.session_state.custom_weights = load_weights()

if "score_overrides" not in st.session_state:
    st.session_state.score_overrides = load_score_overrides()

if "decision_overrides" not in st.session_state:
    st.session_state.decision_overrides = load_decision_overrides()

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

# ── 侧边栏 ──
with st.sidebar:
    st.title("AI量化")
    st.caption("AI驱动 · 人机协同 · ETF策略")
    st.divider()

    pages = {
        "总览仪表盘": "pages/1_dashboard.py",
        "因子分析": "pages/2_analysis.py",
        "决策中心": "pages/3_decision.py",
        "策略回测": "pages/4_backtest.py",
    }

    st.markdown("**导航**")
    for name in pages:
        st.page_link(pages[name], label=name)

    st.divider()

    if st.session_state.last_refresh:
        st.caption(f"最后更新: {st.session_state.last_refresh.strftime('%H:%M')}")

    if st.session_state.decision_overrides:
        st.warning(f"⚠️ 存在 {len(st.session_state.decision_overrides)} 个人工干预")

# ── 主页（重定向到仪表盘）──
st.title("AI量化投资系统")
st.markdown("""
> 基于**多因子量化模型** + **Claude AI分析**的A股ETF智能决策平台

**系统功能**：
- **宏观经济评分** — PMI、利率、市场趋势综合分析
- **板块轮动检测** — 识别当前强势/弱势板块
- **多因子打分** — 动量、量能、趋势、基本面
- **AI情绪分析** — Claude解读市场新闻
- **人机协同决策** — 三层干预机制，量化为主、人工为辅

**请通过侧边栏导航或点击下方按钮开始**
""")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("pages/1_dashboard.py", label="总览仪表盘", icon="📊")
with col2:
    st.page_link("pages/2_analysis.py", label="因子分析", icon="🔍")
with col3:
    st.page_link("pages/3_decision.py", label="决策中心", icon="🎯")
with col4:
    st.page_link("pages/4_backtest.py", label="策略回测", icon="📈")
