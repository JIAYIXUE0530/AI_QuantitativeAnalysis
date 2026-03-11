"""
现代金融风格配色 - 参考主流商业分析工具
"""

THINKCELL_CSS = """
<style>
/* ── 全局字体 ── */
html, body, [class*="css"] {
    font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
}

/* ── 主内容区背景 ── */
.main .block-container {
    background: #F5F7FA;
    padding-top: 1.5rem;
}

/* ── 标题 ── */
h1 {
    color: #0D1B2A !important;
    font-weight: 700 !important;
    font-size: 1.6em !important;
    border-bottom: 3px solid #1677FF;
    padding-bottom: 10px;
    margin-bottom: 16px;
}
h2 { color: #0D1B2A !important; font-weight: 600 !important; }
h3 { color: #1677FF !important; font-weight: 600 !important; }

/* ── 主按钮 ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1677FF 0%, #0EA5E9 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.4rem 1.2rem !important;
    box-shadow: 0 2px 8px rgba(22,119,255,0.35) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 16px rgba(22,119,255,0.5) !important;
    opacity: 0.92 !important;
}

/* ── 次级按钮 ── */
.stButton > button {
    border: 1.5px solid #1677FF !important;
    color: #1677FF !important;
    border-radius: 8px !important;
    background: white !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    background: #EFF6FF !important;
}

/* ── Metric 卡片 ── */
[data-testid="metric-container"] {
    background: white;
    border-radius: 12px;
    padding: 16px 18px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-top: 3px solid #1677FF;
}
[data-testid="metric-container"] label {
    color: #6B7280 !important;
    font-weight: 500;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0D1B2A !important;
    font-size: 1.7em !important;
    font-weight: 700 !important;
}

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1B2A 0%, #1E3A5F 100%) !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F0F7FF !important;
    border-bottom: 1px solid rgba(22,119,255,0.4) !important;
}
[data-testid="stSidebar"] .stSlider > div > div {
    background: #1677FF !important;
}

/* ── 数据表格 ── */
[data-testid="stDataFrame"] thead th {
    background: #1677FF !important;
    color: white !important;
    font-weight: 600 !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background: #F0F7FF !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background: #DBEAFE !important;
}

/* ── 信号颜色 ── */
.signal-buy  { color: #DC2626; font-weight: 700; }
.signal-sell { color: #16A34A; font-weight: 700; }
.signal-hold { color: #D97706; font-weight: 700; }

/* ── AI 分析卡片 ── */
.claude-card {
    background: linear-gradient(135deg, #EFF6FF 0%, #F0F9FF 100%);
    border-left: 4px solid #1677FF;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #0D1B2A;
    font-size: 0.95em;
    line-height: 1.7;
    box-shadow: 0 2px 8px rgba(22,119,255,0.08);
}

/* ── Override 徽章 ── */
.override-badge {
    background: linear-gradient(135deg, #F59E0B, #EF4444);
    color: white;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}

/* ── Factor override 高亮 ── */
.factor-override {
    background: #FFFBEB;
    border: 1px solid #F59E0B;
    border-radius: 6px;
    padding: 3px 6px;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    background: white !important;
}
[data-testid="stExpander"] summary {
    color: #0D1B2A !important;
    font-weight: 600 !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #1677FF, #0EA5E9) !important;
    border-radius: 4px !important;
}

/* ── Tab 组件 ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: white;
    border-radius: 10px;
    padding: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    color: #6B7280 !important;
    font-weight: 500;
    border-radius: 8px !important;
}
.stTabs [aria-selected="true"] {
    background: #1677FF !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ── 分割线 ── */
hr { border-color: #E2E8F0 !important; }


</style>
"""

# 配色常量（供图表使用）
TC_BLUE_DARK   = "#0D1B2A"
TC_BLUE_MID    = "#1677FF"
TC_BLUE_LIGHT  = "#0EA5E9"
TC_BLUE_PALE   = "#EFF6FF"
TC_RED         = "#DC2626"
TC_GREEN       = "#16A34A"
TC_ORANGE      = "#D97706"
TC_GRAY        = "#6B7280"
