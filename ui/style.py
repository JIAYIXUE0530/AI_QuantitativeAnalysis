"""
ThinkCell Blue 统一样式 - 所有页面共享
"""

THINKCELL_CSS = """
<style>
/* ── 全局字体与背景 ── */
html, body, [class*="css"] {
    font-family: "Calibri", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── 顶部标题栏 ── */
h1 { color: #1F3864 !important; border-bottom: 3px solid #5B9BD5; padding-bottom: 8px; }
h2 { color: #1F3864 !important; }
h3 { color: #5B9BD5 !important; }

/* ── 主按钮 ── */
.stButton > button[kind="primary"] {
    background-color: #5B9BD5 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #1F5C96 !important;
}

/* ── 次级按钮 ── */
.stButton > button {
    border: 1.5px solid #5B9BD5 !important;
    color: #5B9BD5 !important;
    border-radius: 4px !important;
}

/* ── Metric 卡片 ── */
[data-testid="metric-container"] {
    background: #DEEAF1;
    border-left: 4px solid #5B9BD5;
    border-radius: 6px;
    padding: 10px 14px !important;
}
[data-testid="metric-container"] label {
    color: #5B9BD5 !important;
    font-weight: 600;
    font-size: 0.82em;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1F3864 !important;
    font-size: 1.6em !important;
    font-weight: 700 !important;
}

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: #1F3864 !important;
}
[data-testid="stSidebar"] * {
    color: #DEEAF1 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #BDD7EE !important;
    border-bottom: 1px solid #5B9BD5 !important;
}
[data-testid="stSidebar"] .stSlider > div > div {
    background: #5B9BD5 !important;
}

/* ── 数据表格 ── */
[data-testid="stDataFrame"] thead {
    background: #5B9BD5 !important;
}
[data-testid="stDataFrame"] thead th {
    color: white !important;
    font-weight: 600 !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background: #DEEAF1 !important;
}

/* ── 信号颜色 ── */
.signal-buy  { color: #C00000; font-weight: 700; }
.signal-sell { color: #375623; font-weight: 700; }
.signal-hold { color: #ED7D31; font-weight: 700; }

/* ── Claude / AI 卡片 ── */
.claude-card {
    background: #DEEAF1;
    border-left: 4px solid #5B9BD5;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #1F3864;
    font-size: 0.95em;
    line-height: 1.6;
}

/* ── Override 徽章 ── */
.override-badge {
    background: #ED7D31;
    color: white;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Factor override 高亮 ── */
.factor-override {
    background: #FFF2CC;
    border: 1px solid #ED7D31;
    border-radius: 4px;
    padding: 3px 6px;
}

/* ── Expander ── */
[data-testid="stExpander"] summary {
    color: #1F3864 !important;
    font-weight: 600 !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div {
    background-color: #5B9BD5 !important;
}

/* ── Info / Warning / Success ── */
[data-testid="stAlert"][data-baseweb="notification"] {
    border-radius: 6px;
}

/* ── Tab 组件 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #5B9BD5 !important;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    border-bottom: 3px solid #5B9BD5 !important;
    color: #1F3864 !important;
}

/* ── 分割线 ── */
hr { border-color: #BDD7EE !important; }
</style>
"""

# ThinkCell 配色常量（供图表使用）
TC_BLUE_DARK   = "#1F3864"
TC_BLUE_MID    = "#5B9BD5"
TC_BLUE_LIGHT  = "#BDD7EE"
TC_BLUE_PALE   = "#DEEAF1"
TC_RED         = "#C00000"
TC_GREEN       = "#375623"
TC_ORANGE      = "#ED7D31"
TC_GRAY        = "#595959"
