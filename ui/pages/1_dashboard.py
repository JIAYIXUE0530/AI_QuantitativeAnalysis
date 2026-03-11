"""
总览仪表盘 - 市场概览、Top picks、宏观状态
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime

from config.settings import config, WeightConfig
from core.pipeline import run_full_pipeline
from ui.components.charts import (
    render_sector_heatmap, render_macro_radar, render_score_gauge
)
from ui.style import THINKCELL_CSS

st.set_page_config(page_title="总览仪表盘", layout="wide", page_icon=None)
st.markdown(THINKCELL_CSS, unsafe_allow_html=True)

# ── Session State 初始化 ──
for key, default in [
    ("pipeline_state", None),
    ("custom_weights", config.default_weights.to_dict()),
    ("score_overrides", {}),
    ("decision_overrides", {}),
    ("last_refresh", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _refresh_analysis():
    weights = WeightConfig(**st.session_state.custom_weights)
    progress_bar = st.progress(0, text="正在分析...")

    def on_progress(msg, pct):
        progress_bar.progress(int(pct), text=msg)

    with st.spinner(""):
        state = run_full_pipeline(
            weights=weights,
            score_overrides=st.session_state.score_overrides,
            decision_overrides=st.session_state.decision_overrides,
            progress_callback=on_progress,
        )
    st.session_state.pipeline_state = state
    st.session_state.last_refresh = datetime.now()
    progress_bar.empty()
    st.rerun()


# ── 顶部控制栏 ──
st.title("总览仪表盘")

col_btn, col_time, col_warn = st.columns([2, 3, 3])
with col_btn:
    if st.button("刷新分析", type="primary", use_container_width=True):
        _refresh_analysis()
with col_time:
    if st.session_state.last_refresh:
        st.info(f"最后更新: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("点击「刷新分析」开始")
with col_warn:
    if st.session_state.decision_overrides:
        st.warning(f"存在 {len(st.session_state.decision_overrides)} 个人工决策干预")

state = st.session_state.pipeline_state

if state is None:
    st.markdown("""
    <div style="margin-top:2rem;padding:32px 36px;background:white;border-radius:12px;
                border:1px solid #E8EDF5;box-shadow:0 2px 12px rgba(0,0,0,0.04)">
        <h3 style="color:#0D1B2A;margin-bottom:16px;font-size:1.1rem">开始使用</h3>
        <p style="color:#6B7280;margin-bottom:20px;font-size:0.9rem;line-height:1.7">
            点击右上角「刷新分析」按钮，系统将自动完成以下步骤：
        </p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div style="padding:14px 16px;background:#F8FAFF;border-radius:8px;border:1px solid #E8EDF5">
                <div style="color:#1677FF;font-weight:600;font-size:0.82rem;margin-bottom:4px">STEP 01</div>
                <div style="color:#374151;font-size:0.88rem">获取 25 只 A 股 ETF 历史价格数据</div>
            </div>
            <div style="padding:14px 16px;background:#F8FAFF;border-radius:8px;border:1px solid #E8EDF5">
                <div style="color:#1677FF;font-weight:600;font-size:0.82rem;margin-bottom:4px">STEP 02</div>
                <div style="color:#374151;font-size:0.88rem">计算宏观、板块轮动、多因子评分</div>
            </div>
            <div style="padding:14px 16px;background:#F8FAFF;border-radius:8px;border:1px solid #E8EDF5">
                <div style="color:#1677FF;font-weight:600;font-size:0.82rem;margin-bottom:4px">STEP 03</div>
                <div style="color:#374151;font-size:0.88rem">AI 分析市场新闻，生成情绪评分</div>
            </div>
            <div style="padding:14px 16px;background:#F8FAFF;border-radius:8px;border:1px solid #E8EDF5">
                <div style="color:#1677FF;font-weight:600;font-size:0.82rem;margin-bottom:4px">STEP 04</div>
                <div style="color:#374151;font-size:0.88rem">输出综合排名与买卖建议，首次约 20 秒</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if state.errors:
    for err in state.errors:
        st.error(f"分析异常: {err}")

# ── 宏观状态栏 ──
st.divider()
st.subheader("宏观环境")

if state.macro_score:
    macro = state.macro_score
    m_cols = st.columns(5)

    with m_cols[0]:
        st.plotly_chart(render_score_gauge(macro.score, "宏观综合"),
                        use_container_width=True, key="macro_gauge")

    sub = macro.sub_scores
    indicators = [
        ("pmi", "PMI景气度", "制造业"),
        ("cpi", "CPI通胀", "消费价格"),
        ("bond_yield", "利率环境", "10年国债"),
        ("market_trend", "市场趋势", "上证20日"),
    ]
    for i, (key, label, unit) in enumerate(indicators):
        if key in sub:
            with m_cols[i + 1]:
                s = sub[key]
                color = "normal" if s.score >= 50 else "inverse"
                st.metric(
                    label=label,
                    value=f"{s.value:.1f}",
                    delta=s.signal,
                    delta_color=color,
                )

    # 宏观解释
    st.caption(f"AI解读: {macro.explanation}")

# ── Claude 执行摘要 ──
if state.orchestrator and state.orchestrator.executive_summary:
    st.divider()
    st.markdown(f"""
    <div class="claude-card">
    <b>Claude AI 市场综合判断</b><br>
    {state.orchestrator.executive_summary}
    </div>
    """, unsafe_allow_html=True)

    if state.orchestrator.key_risks:
        with st.expander("风险提示"):
            for risk in state.orchestrator.key_risks:
                st.markdown(f"- {risk}")

# ── 核心内容：三列布局 ──
st.divider()
left_col, mid_col, right_col = st.columns([2, 2, 3])

# 左：买入推荐
with left_col:
    st.subheader("买入推荐")
    buy_list = [s for s in state.composite_scores if s.signal == "BUY"][:5]
    if buy_list:
        for s in buy_list:
            is_override = s.etf_code in st.session_state.decision_overrides
            override_tag = '<span class="override-badge">人工</span>' if is_override else ""
            rationale = ""
            if state.orchestrator and s.etf_code in state.orchestrator.top_picks_rationale:
                rationale = state.orchestrator.top_picks_rationale[s.etf_code]

            st.markdown(f"""
            **{s.etf_name}** `{s.etf_code}` {override_tag}
            - 综合评分: **{s.composite_score:.0f}** | 板块: {s.sector}
            - 置信度: {s.confidence:.0%}
            {f'- *{rationale}*' if rationale else ''}
            """, unsafe_allow_html=True)
            st.progress(s.composite_score / 100)
    else:
        st.info("当前无买入信号")

# 中：关注/观望
with mid_col:
    st.subheader("关注候选")
    hold_list = [s for s in state.composite_scores
                 if s.signal == "HOLD" and s.composite_score >= 55][:5]
    if hold_list:
        for s in hold_list:
            st.markdown(f"""
            **{s.etf_name}** `{s.etf_code}`
            - 综合: {s.composite_score:.0f}分 | {s.sector}
            """)
    else:
        st.info("暂无候选")

    st.divider()
    st.subheader("情绪概览")
    if state.sentiment:
        sent = state.sentiment
        val = sent.overall_sentiment
        label = "乐观" if val > 0.2 else ("悲观" if val < -0.2 else "中性")
        color = "#DC2626" if val > 0.2 else ("#16A34A" if val < -0.2 else "#6B7280")
        st.markdown(f"整体情绪: <span style='color:{color};font-weight:bold'>{label} ({val:+.2f})</span>",
                    unsafe_allow_html=True)
        if sent.key_catalysts:
            st.caption("利好: " + " · ".join(sent.key_catalysts[:2]))
        if sent.key_risks:
            st.caption("风险: " + " · ".join(sent.key_risks[:2]))

# 右：板块热力图
with right_col:
    st.subheader("板块轮动")
    if state.rotation_signals:
        fig = render_sector_heatmap(state.rotation_signals)
        st.plotly_chart(fig, use_container_width=True, key="sector_heatmap")
    else:
        st.info("板块数据加载中")

# ── 完整排名表 ──
st.divider()
st.subheader("ETF完整排名")

if state.composite_scores:
    rows = []
    for s in state.composite_scores:
        is_override = s.etf_code in st.session_state.decision_overrides
        prefix = "[人工] " if is_override else ""
        rows.append({
            "排名": s.rank,
            "代码": s.etf_code,
            "名称": s.etf_name,
            "板块": s.sector,
            "综合评分": s.composite_score,
            "宏观": int(s.raw_scores.get('macro', 0)),
            "轮动": int(s.raw_scores.get('rotation', 0)),
            "动量": int(s.raw_scores.get('momentum', 0)),
            "量能": int(s.raw_scores.get('volume', 0)),
            "趋势": int(s.raw_scores.get('trend', 0)),
            "情绪": int(s.raw_scores.get('sentiment', 0)),
            "信号": f"{prefix}{s.signal}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "综合评分": st.column_config.ProgressColumn(
                "综合评分", min_value=0, max_value=100, format="%.1f"
            ),
            "宏观": st.column_config.NumberColumn("宏观", format="%d"),
            "轮动": st.column_config.NumberColumn("轮动", format="%d"),
            "动量": st.column_config.NumberColumn("动量", format="%d"),
            "量能": st.column_config.NumberColumn("量能", format="%d"),
            "趋势": st.column_config.NumberColumn("趋势", format="%d"),
            "情绪": st.column_config.NumberColumn("情绪", format="%d"),
        }
    )
