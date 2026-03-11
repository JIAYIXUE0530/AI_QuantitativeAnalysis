"""
因子分析页 - 深入分析单只ETF的因子构成
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config.settings import config
from core.data_fetcher import fetcher
from core.models import CompositeScore
from ui.components.charts import (
    render_factor_waterfall, render_macro_radar, render_sector_heatmap
)
from ui.style import THINKCELL_CSS

st.set_page_config(page_title="因子分析", layout="wide")
st.markdown(THINKCELL_CSS, unsafe_allow_html=True)

for key, default in [
    ("pipeline_state", None),
    ("custom_weights", config.default_weights.to_dict()),
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.title("因子深度分析")
state = st.session_state.pipeline_state

if state is None:
    st.warning("请先在「总览仪表盘」执行分析")
    st.stop()

# ── ETF选择器 ──
universe = fetcher.get_etf_universe()
etf_options = {f"{e['name']} ({e['code']})": e["code"] for e in universe}
selected_label = st.selectbox("选择要分析的ETF", list(etf_options.keys()))
selected_code = etf_options[selected_label]

# 找到该ETF的分析结果
score: CompositeScore = None
for s in state.composite_scores:
    if s.etf_code == selected_code:
        score = s
        break

if score is None:
    st.error(f"未找到 {selected_code} 的分析结果，请重新刷新")
    st.stop()

# ── 顶部评分概览 ──
st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
signal_color = {"BUY": "#DC2626", "SELL": "#16A34A", "HOLD": "#D97706"}
with m1:
    st.metric("综合评分", f"{score.composite_score:.1f}", f"排名 #{score.rank}")
with m2:
    color = signal_color.get(score.signal, "#6B7280")
    st.markdown(f"**信号**<br><span style='color:{color};font-size:1.5em'>{score.signal}</span>",
                unsafe_allow_html=True)
with m3:
    st.metric("板块", score.sector)
with m4:
    st.metric("置信度", f"{score.confidence:.0%}")
with m5:
    adj = score.claude_adjustment
    st.metric("Claude调整", f"{adj:+.1f}分",
              delta_color="normal" if adj >= 0 else "inverse")

# ── 因子瀑布图 ──
st.divider()
st.subheader("因子贡献分解")

col_chart, col_detail = st.columns([3, 2])

with col_chart:
    fig = render_factor_waterfall(score)
    st.plotly_chart(fig, use_container_width=True, key="waterfall")

with col_detail:
    st.markdown("**各因子原始分（0-100）**")
    factor_labels = {
        "macro": "宏观环境",
        "rotation": "板块轮动",
        "momentum": "价格动量",
        "volume": "成交量能",
        "trend": "趋势强度",
        "fundamental": "基本面",
        "sentiment": "市场情绪",
    }
    for factor, label in factor_labels.items():
        raw = score.raw_scores.get(factor, 0)
        weight = st.session_state.custom_weights.get(factor, 0)
        bar_color = "#DC2626" if raw >= 65 else ("#D97706" if raw >= 45 else "#16A34A")
        st.markdown(f"{label} `×{weight:.0%}`")
        st.progress(raw / 100, text=f"{raw:.0f}分")

# ── 因子详情展开 ──
st.divider()
st.subheader("因子详细数据")

bundle = state.factor_bundles.get(selected_code)
if bundle:
    tab1, tab2, tab3, tab4 = st.tabs(["动量", "量能", "趋势", "基本面"])

    with tab1:
        st.markdown("**动量因子详情**")
        detail = bundle.momentum_detail
        if detail:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("20日收益率", f"{detail.get('ret_20d', 0):.2f}%")
            with c2:
                st.metric("60日收益率", f"{detail.get('ret_60d', 0):.2f}%")
            with c3:
                st.metric("RSI(14)", f"{detail.get('rsi_14', 50):.1f}")
        else:
            st.info("详细数据不可用")

    with tab2:
        st.markdown("**量能因子详情**")
        detail = bundle.volume_detail
        if detail:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("量比", f"{detail.get('vol_ratio', 1):.2f}x")
            with c2:
                obv = detail.get('obv_trend_pct', 0)
                st.metric("OBV趋势", f"{obv:+.2f}%",
                          delta_color="normal" if obv >= 0 else "inverse")
        else:
            st.info("详细数据不可用")

    with tab3:
        st.markdown("**趋势因子详情**")
        detail = bundle.trend_detail
        if detail:
            c1, c2, c3 = st.columns(3)
            with c1:
                ema20 = detail.get('above_ema20', False)
                st.metric("站上EMA20", "是" if ema20 else "否",
                          delta_color="normal" if ema20 else "inverse")
            with c2:
                ema60 = detail.get('above_ema60', False)
                st.metric("站上EMA60", "是" if ema60 else "否",
                          delta_color="normal" if ema60 else "inverse")
            with c3:
                adx = detail.get('adx', 0)
                st.metric("ADX趋势强度", f"{adx:.1f}",
                          "强趋势" if adx > 25 else "弱趋势")
            bb = detail.get('bb_position_pct', 50)
            st.markdown(f"**布林带位置**: {bb:.0f}% (0%=下轨, 100%=上轨)")
            st.progress(bb / 100)
        else:
            st.info("详细数据不可用")

    with tab4:
        st.markdown("**基本面因子详情**")
        detail = bundle.fundamental_detail
        if detail:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("年化波动率", f"{detail.get('annual_volatility_pct', 0):.1f}%")
            with c2:
                pos = detail.get('price_position_pct', 50)
                st.metric("年内价格位置", f"{pos:.0f}%",
                          "高位" if pos > 70 else ("低位" if pos < 30 else "中位"))
            with c3:
                prem = detail.get('premium_discount_pct', 0)
                st.metric("溢折价率", f"{prem:+.2f}%",
                          delta_color="inverse" if abs(prem) > 0.5 else "normal")
        else:
            st.info("详细数据不可用")
else:
    st.warning("因子详细数据不可用")

# ── 价格走势图 ──
st.divider()
st.subheader("价格走势")

try:
    price_df = fetcher.get_price_history(selected_code, days=120)
    if len(price_df) > 0:
        fig = go.Figure()
        close = price_df["close"]

        # K线
        if all(col in price_df.columns for col in ["open", "high", "low", "close"]):
            fig.add_trace(go.Candlestick(
                x=price_df.index,
                open=price_df["open"],
                high=price_df["high"],
                low=price_df["low"],
                close=price_df["close"],
                name="K线",
                increasing_line_color="#DC2626",
                decreasing_line_color="#16A34A",
            ))
        else:
            fig.add_trace(go.Scatter(x=price_df.index, y=close, name="收盘价",
                                      line={"color": "#1E6FBF"}))

        # 均线
        ema20 = close.ewm(span=20).mean()
        ema60 = close.ewm(span=60).mean()
        fig.add_trace(go.Scatter(x=price_df.index, y=ema20,
                                  name="EMA20", line={"color": "#D97706", "dash": "dot"}))
        fig.add_trace(go.Scatter(x=price_df.index, y=ema60,
                                  name="EMA60", line={"color": "#6B7280", "dash": "dot"}))

        fig.update_layout(
            title=f"{score.etf_name} 近120日走势",
            height=400,
            xaxis_rangeslider_visible=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
        )
        st.plotly_chart(fig, use_container_width=True, key="price_chart")
except Exception as e:
    st.warning(f"价格图表加载失败: {e}")

# ── 宏观雷达图 ──
if state.macro_score and state.macro_score.sub_scores:
    st.divider()
    st.subheader("宏观环境雷达")
    fig = render_macro_radar(state.macro_score.sub_scores)
    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(fig, use_container_width=True, key="macro_radar")
    with col2:
        st.markdown("**宏观子指标详情**")
        for name, sub in state.macro_score.sub_scores.items():
            st.markdown(f"- **{sub.description}**: {sub.value:.2f} — {sub.signal} ({sub.score:.0f}分)")
        st.caption(state.macro_score.explanation)
