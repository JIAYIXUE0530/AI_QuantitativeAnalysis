"""
策略回测页
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from config.settings import config, WeightConfig
from core.backtester import run_backtest
from ui.components.charts import render_equity_curve

st.set_page_config(page_title="策略回测 - TRAE", layout="wide", page_icon="📈")

for key, default in [
    ("custom_weights", config.default_weights.to_dict()),
    ("backtest_result", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📈 策略回测")
st.caption("走前向回测（Walk-forward），无前视偏差。回测不使用LLM以避免未来数据问题。")

# ── 参数设置 ──
st.subheader("回测参数设置")

col1, col2, col3, col4 = st.columns(4)

with col1:
    end_date = datetime.now().date()
    default_start = end_date - timedelta(days=365 * 2)
    start_date_input = st.date_input("开始日期", value=default_start,
                                      max_value=end_date - timedelta(days=90))

with col2:
    end_date_input = st.date_input("结束日期", value=end_date,
                                    min_value=start_date_input + timedelta(days=90))

with col3:
    top_n = st.selectbox("持仓ETF数量", [3, 5, 8, 10], index=1)
    rebalance = st.selectbox("调仓频率", ["weekly", "monthly"],
                               format_func=lambda x: "每周" if x == "weekly" else "每月")

with col4:
    cost_bps = st.number_input("交易成本(基点)", value=10.0, min_value=0.0,
                                max_value=50.0, step=1.0)
    st.caption("10bps ≈ 万一，A股ETF通常5-15bps")

# 权重设置（复用当前session权重或自定义）
st.markdown("**因子权重**（可从「决策中心」调整后同步，或在此独立设置）")

use_session_weights = st.checkbox("使用当前会话权重", value=True)

if use_session_weights:
    bt_weights = WeightConfig(**st.session_state.custom_weights).normalize()
    st.caption(f"当前权重: " + " | ".join([f"{k}={v:.0%}" for k, v in bt_weights.to_dict().items()]))
else:
    w_cols = st.columns(7)
    factor_names = ["macro", "rotation", "momentum", "volume", "trend", "fundamental", "sentiment"]
    factor_labels = ["宏观", "轮动", "动量", "量能", "趋势", "基本面", "情绪"]
    default_w = config.default_weights.to_dict()
    custom_w = {}
    for i, (fname, flabel) in enumerate(zip(factor_names, factor_labels)):
        with w_cols[i]:
            custom_w[fname] = st.slider(flabel, 0.0, 1.0,
                                         value=default_w.get(fname, 0.15), step=0.05,
                                         key=f"bt_w_{fname}")
    bt_weights = WeightConfig(**custom_w).normalize()

# ── 运行回测 ──
st.divider()
if st.button("开始回测", type="primary", use_container_width=False):
    with st.spinner("回测运行中，首次可能需要几分钟（需要获取历史数据）..."):
        try:
            result = run_backtest(
                start_date=str(start_date_input),
                end_date=str(end_date_input),
                weights=bt_weights,
                top_n=top_n,
                rebalance=rebalance,
                transaction_cost_bps=cost_bps,
            )
            st.session_state.backtest_result = result
        except Exception as e:
            st.error(f"回测失败: {e}")
            st.exception(e)

# ── 结果展示 ──
result = st.session_state.backtest_result
if result is None:
    st.info("设置参数后点击「开始回测」")
    st.stop()

st.divider()
st.subheader("回测结果")

# 绩效指标
m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    (m1, "年化收益率", f"{result.annual_return:.2f}%",
     f"超额 {result.excess_return:+.2f}%",
     "normal" if result.excess_return >= 0 else "inverse"),
    (m2, "夏普比率", f"{result.sharpe_ratio:.2f}", None, "normal"),
    (m3, "最大回撤", f"{result.max_drawdown:.2f}%", None,
     "inverse" if result.max_drawdown < -10 else "normal"),
    (m4, "胜率", f"{result.win_rate:.1f}%", None, "normal"),
    (m5, "基准年化", f"{result.benchmark_annual_return:.2f}%", "沪深300", "normal"),
    (m6, "总交易次数", str(result.total_trades), None, "normal"),
]

for col, label, val, delta, delta_color in metrics:
    with col:
        if delta:
            st.metric(label, val, delta=delta, delta_color=delta_color)
        else:
            st.metric(label, val)

# 净值曲线
st.divider()
if result.equity_curve is not None and len(result.equity_curve) > 0:
    fig = render_equity_curve(
        result.equity_curve,
        result.benchmark_curve,
        f"Top{top_n} ETF策略"
    )
    st.plotly_chart(fig, use_container_width=True, key="bt_equity")

    # 回撤图
    equity = result.equity_curve
    peak = equity.cummax()
    drawdown = (equity - peak) / peak * 100

    import plotly.graph_objects as go
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values,
        fill="tozeroy", fillcolor="rgba(232,75,75,0.2)",
        line={"color": "#E84B4B"},
        name="回撤"
    ))
    fig_dd.update_layout(
        title="策略回撤曲线",
        yaxis_title="回撤 (%)",
        height=250,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
    )
    st.plotly_chart(fig_dd, use_container_width=True, key="bt_drawdown")

# 交易记录
if result.trades is not None and len(result.trades) > 0:
    st.divider()
    st.subheader("交易记录")
    st.dataframe(result.trades, use_container_width=True, hide_index=True)
    csv = result.trades.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("下载交易记录", data=csv,
                        file_name=f"回测交易_{result.start_date}_{result.end_date}.csv",
                        mime="text/csv")

# 配置摘要
st.divider()
with st.expander("回测配置详情"):
    st.json(result.config_summary)
    st.caption(f"回测区间: {result.start_date} ~ {result.end_date}")
    st.caption("⚠️ 注意：回测结果不代表未来收益。历史绩效仅供参考。")
