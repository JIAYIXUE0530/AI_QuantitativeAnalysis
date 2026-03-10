"""
可复用图表组件
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from core.models import CompositeScore, RotationSignal


def render_factor_waterfall(score: CompositeScore) -> go.Figure:
    """
    瀑布图：展示各因子对综合评分的贡献
    """
    breakdown = score.breakdown
    factors = ["macro", "rotation", "momentum", "volume", "trend", "fundamental", "sentiment"]
    factor_labels = {
        "macro": "宏观环境",
        "rotation": "板块轮动",
        "momentum": "价格动量",
        "volume": "成交量能",
        "trend": "趋势强度",
        "fundamental": "基本面",
        "sentiment": "市场情绪",
    }

    x_labels = [factor_labels.get(f, f) for f in factors]
    values = [breakdown.get(f, 0) for f in factors]

    claude_adj = breakdown.get("claude_adjustment", 0)

    fig = go.Figure(go.Waterfall(
        name="因子贡献",
        orientation="v",
        measure=["relative"] * len(factors) + ["total"],
        x=x_labels + ["Claude调整", "综合评分"],
        textposition="outside",
        text=[f"+{v:.1f}" if v >= 0 else f"{v:.1f}" for v in values] +
             [f"{claude_adj:+.1f}", f"{score.composite_score:.1f}"],
        y=values + [claude_adj, score.composite_score],
        connector={"line": {"color": "rgba(63, 63, 63, 0.3)"}},
        increasing={"marker": {"color": "#E84B4B"}},
        decreasing={"marker": {"color": "#2DB84B"}},
        totals={"marker": {"color": "#1E6FBF", "line": {"color": "#1E6FBF", "width": 2}}},
    ))

    fig.update_layout(
        title=f"{score.etf_name}（{score.etf_code}）因子贡献分解",
        showlegend=False,
        height=400,
        yaxis_title="评分贡献",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
    )
    return fig


def render_sector_heatmap(rotation_signals: dict[str, RotationSignal]) -> go.Figure:
    """
    板块热力图：颜色代表轮动强弱
    """
    if not rotation_signals:
        return go.Figure()

    sectors = list(rotation_signals.keys())
    scores = [rotation_signals[s].score for s in sectors]
    mom_20 = [rotation_signals[s].momentum_20d for s in sectors]
    signals = [rotation_signals[s].signal for s in sectors]

    colors = []
    for sig in signals:
        if sig == "leading":
            colors.append("#E84B4B")
        elif sig == "lagging":
            colors.append("#2DB84B")
        else:
            colors.append("#888888")

    fig = go.Figure(go.Bar(
        x=sectors,
        y=scores,
        marker_color=colors,
        text=[f"{s:.0f}分<br>{m:+.1f}%" for s, m in zip(scores, mom_20)],
        textposition="outside",
    ))

    fig.update_layout(
        title="板块相对强弱排名",
        xaxis_title="",
        yaxis_title="相对强度评分",
        yaxis=dict(range=[0, 110]),
        height=350,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
    )
    return fig


def render_macro_radar(sub_scores: dict) -> go.Figure:
    """
    宏观指标雷达图
    """
    if not sub_scores:
        return go.Figure()

    labels = {
        "pmi": "PMI景气",
        "cpi": "CPI通胀",
        "bond_yield": "利率环境",
        "market_trend": "市场趋势",
    }
    categories = [labels.get(k, k) for k in sub_scores.keys()]
    values = [v.score for v in sub_scores.values()]
    categories.append(categories[0])  # 闭合
    values.append(values[0])

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(30, 111, 191, 0.2)",
        line={"color": "#1E6FBF", "width": 2},
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
        ),
        title="宏观环境雷达图",
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
    )
    return fig


def render_equity_curve(equity: pd.Series,
                         benchmark: pd.Series,
                         strategy_name: str = "策略") -> go.Figure:
    """
    净值曲线对比图（策略 vs 基准）
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values,
        name=strategy_name,
        line={"color": "#E84B4B", "width": 2},
    ))

    fig.add_trace(go.Scatter(
        x=benchmark.index, y=benchmark.values,
        name="沪深300基准",
        line={"color": "#888888", "width": 1.5, "dash": "dash"},
    ))

    fig.update_layout(
        title="策略净值曲线",
        xaxis_title="日期",
        yaxis_title="净值",
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "PingFang SC, Microsoft YaHei, sans-serif"},
        legend={"orientation": "h", "y": -0.15},
    )
    return fig


def render_score_gauge(score: float, title: str = "综合评分") -> go.Figure:
    """
    仪表盘样式的单个评分显示
    """
    if score >= 65:
        color = "#E84B4B"
    elif score >= 40:
        color = "#F0A500"
    else:
        color = "#2DB84B"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "rgba(45,184,75,0.2)"},
                {"range": [40, 65], "color": "rgba(240,165,0,0.2)"},
                {"range": [65, 100], "color": "rgba(232,75,75,0.2)"},
            ],
        },
    ))
    fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                       font={"family": "PingFang SC, Microsoft YaHei, sans-serif"})
    return fig
