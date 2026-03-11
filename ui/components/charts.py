"""
可复用图表组件 - ThinkCell Blue 配色
"""
import plotly.graph_objects as go
import pandas as pd
from core.models import CompositeScore, RotationSignal

# ThinkCell Blue 配色
TC_DARK   = "#1F3864"
TC_MID    = "#5B9BD5"
TC_LIGHT  = "#BDD7EE"
TC_PALE   = "#DEEAF1"
TC_RED    = "#C00000"
TC_GREEN  = "#375623"
TC_ORANGE = "#ED7D31"
TC_GRAY   = "#595959"

_FONT = {"family": "Calibri, PingFang SC, Microsoft YaHei, sans-serif",
         "color": TC_DARK}
_LAYOUT_BASE = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=_FONT,
    title_font={"color": TC_DARK, "size": 14, "family": "Calibri, PingFang SC, sans-serif"},
)


def render_factor_waterfall(score: CompositeScore) -> go.Figure:
    """瀑布图：各因子对综合评分的贡献"""
    breakdown = score.breakdown
    factors = ["macro", "rotation", "momentum", "volume", "trend", "fundamental", "sentiment"]
    labels = {
        "macro": "宏观环境", "rotation": "板块轮动", "momentum": "价格动量",
        "volume": "成交量能", "trend": "趋势强度", "fundamental": "基本面",
        "sentiment": "市场情绪",
    }
    x = [labels[f] for f in factors]
    y = [breakdown.get(f, 0) for f in factors]
    claude_adj = breakdown.get("claude_adjustment", 0)

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative"] * len(factors) + ["relative", "total"],
        x=x + ["AI调整", "综合评分"],
        y=y + [claude_adj, score.composite_score],
        textposition="outside",
        text=[f"+{v:.1f}" if v >= 0 else f"{v:.1f}" for v in y] +
             [f"{claude_adj:+.1f}", f"{score.composite_score:.1f}"],
        connector={"line": {"color": TC_LIGHT, "width": 1}},
        increasing={"marker": {"color": TC_MID}},
        decreasing={"marker": {"color": TC_RED}},
        totals={"marker": {"color": TC_DARK, "line": {"color": TC_DARK, "width": 2}}},
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=f"{score.etf_name}（{score.etf_code}）因子贡献分解",
        showlegend=False,
        height=400,
        yaxis_title="评分贡献",
        yaxis={"gridcolor": TC_PALE, "zerolinecolor": TC_LIGHT},
        xaxis={"tickfont": {"size": 11}},
    )
    return fig


def render_sector_heatmap(rotation_signals: dict[str, RotationSignal]) -> go.Figure:
    """板块相对强弱柱状图"""
    if not rotation_signals:
        return go.Figure()

    sectors = list(rotation_signals.keys())
    scores  = [rotation_signals[s].score for s in sectors]
    mom_20  = [rotation_signals[s].momentum_20d for s in sectors]
    sigs    = [rotation_signals[s].signal for s in sectors]

    # 按强弱排序
    sorted_data = sorted(zip(sectors, scores, mom_20, sigs), key=lambda x: x[1], reverse=True)
    sectors, scores, mom_20, sigs = zip(*sorted_data)

    colors = [TC_MID if s == "leading" else (TC_LIGHT if s == "neutral" else TC_PALE)
              for s in sigs]
    border = [TC_DARK if s == "leading" else TC_MID for s in sigs]

    fig = go.Figure(go.Bar(
        x=list(sectors),
        y=list(scores),
        marker={"color": colors, "line": {"color": border, "width": 1.5}},
        text=[f"{s:.0f}分<br>{m:+.1f}%" for s, m in zip(scores, mom_20)],
        textposition="outside",
        textfont={"color": TC_DARK, "size": 11},
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title="板块相对强弱排名",
        yaxis={"range": [0, 115], "gridcolor": TC_PALE, "title": "相对强度评分"},
        xaxis={"tickfont": {"size": 11}},
        height=350,
    )
    return fig


def render_macro_radar(sub_scores: dict) -> go.Figure:
    """宏观指标雷达图"""
    if not sub_scores:
        return go.Figure()

    label_map = {
        "pmi": "PMI景气", "cpi": "CPI通胀",
        "bond_yield": "利率环境", "market_trend": "市场趋势",
    }
    cats = [label_map.get(k, k) for k in sub_scores.keys()]
    vals = [v.score for v in sub_scores.values()]
    cats.append(cats[0])
    vals.append(vals[0])

    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor=f"rgba(46,117,182,0.15)",
        line={"color": TC_MID, "width": 2},
        marker={"color": TC_MID, "size": 6},
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        polar=dict(
            bgcolor=TC_PALE,
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor=TC_LIGHT, tickfont={"size": 9}),
            angularaxis=dict(gridcolor=TC_LIGHT),
        ),
        title="宏观环境雷达图",
        height=320,
    )
    return fig


def render_equity_curve(equity: pd.Series,
                         benchmark: pd.Series,
                         strategy_name: str = "策略") -> go.Figure:
    """净值曲线对比图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values, name=strategy_name,
        line={"color": TC_MID, "width": 2.5},
        fill="tozeroy", fillcolor="rgba(46,117,182,0.08)",
    ))
    fig.add_trace(go.Scatter(
        x=benchmark.index, y=benchmark.values, name="沪深300基准",
        line={"color": TC_GRAY, "width": 1.5, "dash": "dot"},
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title="策略净值曲线",
        xaxis_title="日期",
        yaxis={"title": "净值", "gridcolor": TC_PALE},
        height=400,
        legend={"orientation": "h", "y": -0.15,
                "bgcolor": "white", "bordercolor": TC_LIGHT},
        hovermode="x unified",
    )
    return fig


def render_score_gauge(score: float, title: str = "综合评分") -> go.Figure:
    """仪表盘评分"""
    if score >= 65:
        bar_color = TC_MID
        step_colors = [TC_PALE, TC_LIGHT, TC_MID]
    elif score >= 40:
        bar_color = TC_ORANGE
        step_colors = [TC_PALE, "#FAE5D3", "#F5CBA7"]
    else:
        bar_color = TC_RED
        step_colors = ["#FADBD8", "#F1948A", TC_RED]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title, "font": {"size": 13, "color": TC_DARK}},
        number={"font": {"color": TC_DARK, "size": 32}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": TC_GRAY,
                     "tickfont": {"size": 10}},
            "bar": {"color": bar_color, "thickness": 0.3},
            "bgcolor": TC_PALE,
            "bordercolor": TC_LIGHT,
            "steps": [
                {"range": [0, 40],  "color": step_colors[0]},
                {"range": [40, 65], "color": step_colors[1]},
                {"range": [65, 100],"color": step_colors[2]},
            ],
        },
    ))
    fig.update_layout(
        height=210,
        paper_bgcolor="white",
        font=_FONT,
        margin={"t": 40, "b": 10, "l": 20, "r": 20},
    )
    return fig
