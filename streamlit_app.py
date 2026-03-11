"""
Streamlit Cloud 入口
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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

for key, loader in [
    ("pipeline_state", lambda: None),
    ("custom_weights", load_weights),
    ("score_overrides", load_score_overrides),
    ("decision_overrides", load_decision_overrides),
    ("last_refresh", lambda: None),
]:
    if key not in st.session_state:
        st.session_state[key] = loader()

with st.sidebar:
    st.title("AI量化")
    st.caption("AI驱动 · 人机协同 · ETF策略")
    st.divider()
    if st.session_state.last_refresh:
        st.caption(f"最后更新: {st.session_state.last_refresh.strftime('%H:%M')}")
    if st.session_state.decision_overrides:
        st.warning(f"⚠️ 存在 {len(st.session_state.decision_overrides)} 个人工干预")

st.title("AI量化投资系统")
st.markdown("""
> 基于**多因子量化模型** + **AI分析**的A股ETF智能决策平台

**系统功能**：
- **宏观经济评分** — PMI、利率、市场趋势综合分析
- **板块轮动检测** — 识别当前强势/弱势板块
- **多因子打分** — 动量、量能、趋势、基本面
- **AI情绪分析** — LLM解读市场新闻
- **人机协同决策** — 三层干预机制，量化为主、人工为辅
""")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("ui/pages/1_dashboard.py", label="总览仪表盘", icon="📊")
with col2:
    st.page_link("ui/pages/2_analysis.py", label="因子分析", icon="🔍")
with col3:
    st.page_link("ui/pages/3_decision.py", label="决策中心", icon="🎯")
with col4:
    st.page_link("ui/pages/4_backtest.py", label="策略回测", icon="📈")
