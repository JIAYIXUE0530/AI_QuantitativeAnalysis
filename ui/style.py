"""
现代金融风格 UI - 专业、简洁、无表情包
"""

THINKCELL_CSS = """
<style>
/* ════════════════════════════════════════
   基础重置
════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
}

/* ════════════════════════════════════════
   主内容区
════════════════════════════════════════ */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ════════════════════════════════════════
   标题层级
════════════════════════════════════════ */
h1 {
    color: #0D1B2A !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    border-bottom: 2px solid #1677FF;
    padding-bottom: 10px;
    margin-bottom: 20px !important;
}
h2 {
    color: #0D1B2A !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    margin-top: 1.5rem !important;
}
h3 {
    color: #1677FF !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

/* ════════════════════════════════════════
   按钮
════════════════════════════════════════ */
.stButton > button[kind="primary"] {
    background: #1677FF !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.45rem 1.4rem !important;
    letter-spacing: 0.02em;
    box-shadow: 0 1px 4px rgba(22,119,255,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #0E5FD8 !important;
}
.stButton > button {
    border: 1px solid #D0D7E3 !important;
    color: #374151 !important;
    border-radius: 6px !important;
    background: white !important;
    font-size: 0.88rem !important;
}
.stButton > button:hover {
    border-color: #1677FF !important;
    color: #1677FF !important;
}

/* ════════════════════════════════════════
   Metric 指标卡片
════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: white;
    border-radius: 10px;
    padding: 14px 16px !important;
    border: 1px solid #E8EDF5;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
[data-testid="metric-container"] label {
    color: #6B7280 !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0D1B2A !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* ════════════════════════════════════════
   侧边栏
════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #1677FF !important;
    border-right: none;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.85) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong {
    color: white !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] .stSlider label {
    color: rgba(255,255,255,0.9) !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {
    color: white !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button {
    border-color: rgba(255,255,255,0.4) !important;
    color: white !important;
    background: rgba(255,255,255,0.12) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.22) !important;
}

/* ════════════════════════════════════════
   표 / DataFrame
════════════════════════════════════════ */
[data-testid="stDataFrame"] table {
    border-collapse: collapse;
}
[data-testid="stDataFrame"] thead th {
    background: #1677FF !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.03em;
    padding: 10px 12px !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: #F8FAFF !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: #EFF6FF !important;
}
[data-testid="stDataFrame"] tbody td {
    font-size: 0.85rem !important;
    padding: 8px 12px !important;
    border-bottom: 1px solid #F0F4FA !important;
}

/* ════════════════════════════════════════
   信号标签（纯文字，无表情）
════════════════════════════════════════ */
.signal-buy {
    display: inline-block;
    background: #FEF2F2;
    color: #DC2626;
    font-weight: 700;
    font-size: 0.78rem;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid #FECACA;
    letter-spacing: 0.04em;
}
.signal-sell {
    display: inline-block;
    background: #F0FDF4;
    color: #16A34A;
    font-weight: 700;
    font-size: 0.78rem;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid #BBF7D0;
    letter-spacing: 0.04em;
}
.signal-hold {
    display: inline-block;
    background: #FFFBEB;
    color: #D97706;
    font-weight: 700;
    font-size: 0.78rem;
    padding: 2px 10px;
    border-radius: 20px;
    border: 1px solid #FDE68A;
    letter-spacing: 0.04em;
}

/* ════════════════════════════════════════
   AI 分析卡片
════════════════════════════════════════ */
.claude-card {
    background: #F8FBFF;
    border: 1px solid #DBEAFE;
    border-left: 4px solid #1677FF;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #1E3A5F;
    font-size: 0.9rem;
    line-height: 1.75;
}
.claude-card b {
    color: #1677FF;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ════════════════════════════════════════
   人工干预徽章
════════════════════════════════════════ */
.override-badge {
    display: inline-block;
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
    padding: 1px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.factor-override {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.82rem;
    color: #92400E;
}

/* ════════════════════════════════════════
   Expander
════════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid #E8EDF5 !important;
    border-radius: 8px !important;
    background: white !important;
    margin-bottom: 6px;
}
[data-testid="stExpander"] summary {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 14px;
}
[data-testid="stExpander"] summary:hover {
    background: #F8FAFF !important;
}

/* ════════════════════════════════════════
   Progress bar
════════════════════════════════════════ */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #1677FF, #60AFFE) !important;
    border-radius: 3px !important;
}

/* ════════════════════════════════════════
   Tabs
════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: #F8FAFF;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
    border: 1px solid #E8EDF5;
}
.stTabs [data-baseweb="tab"] {
    color: #6B7280 !important;
    font-weight: 500 !important;
    font-size: 0.87rem !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #1677FF !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(22,119,255,0.3) !important;
}

/* ════════════════════════════════════════
   Alert / Info / Warning
════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 0.88rem !important;
}

/* ════════════════════════════════════════
   Select / Input
════════════════════════════════════════ */
[data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div > div {
    border-radius: 6px !important;
    border-color: #D0D7E3 !important;
}
[data-testid="stSelectbox"] > div:focus-within,
[data-testid="stTextInput"] > div > div:focus-within {
    border-color: #1677FF !important;
    box-shadow: 0 0 0 2px rgba(22,119,255,0.15) !important;
}

/* ════════════════════════════════════════
   Divider
════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 1px solid #E8EDF5 !important;
    margin: 1.5rem 0 !important;
}

/* ════════════════════════════════════════
   Caption / small text
════════════════════════════════════════ */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #9CA3AF !important;
    font-size: 0.8rem !important;
}

/* ════════════════════════════════════════
   Popover
════════════════════════════════════════ */
[data-testid="stPopover"] button {
    font-size: 0.82rem !important;
}
</style>
"""

# 配色常量（供图表使用）
TC_BLUE_DARK   = "#0D1B2A"
TC_BLUE_MID    = "#1677FF"
TC_BLUE_LIGHT  = "#60AFFE"
TC_BLUE_PALE   = "#EFF6FF"
TC_RED         = "#DC2626"
TC_GREEN       = "#16A34A"
TC_ORANGE      = "#D97706"
TC_GRAY        = "#6B7280"
