"""
使用手册页
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from ui.style import THINKCELL_CSS

st.set_page_config(page_title="使用手册", layout="wide", page_icon=None)
st.markdown(THINKCELL_CSS, unsafe_allow_html=True)

st.title("使用手册")
st.caption("本系统专为非金融背景用户设计，所有指标均有通俗解释")

st.divider()

# ══════════════════════════════════════════
# 1. 系统是什么
# ══════════════════════════════════════════
st.subheader("系统是什么")
st.markdown("""
**一句话**：用数学模型和 AI 替你分析 25 只 A 股 ETF，告诉你应该买哪个、持有哪个、卖哪个。

**什么是 ETF？**

ETF（交易型基金）是把一篮子股票打包在一起的基金，可以像股票一样在交易所买卖。
比如"沪深300ETF（510300）"就是同时买入沪深300指数里 300 家公司的股票。
相比单独买股票，ETF 的好处是：**分散风险、费用低、透明度高**。

本系统覆盖的 25 只 ETF 包括宽基指数（沪深300、中证500）、行业板块（半导体、新能源、消费、医疗等），以及债券和黄金，基本覆盖了普通投资者的主要选择。
""")

st.divider()

# ══════════════════════════════════════════
# 2. 四个页面
# ══════════════════════════════════════════
st.subheader("四个页面的用途")

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;'
        'padding:20px 22px;margin-bottom:12px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:8px">总览仪表盘</div>'
        '<div style="color:#2C3A4A;font-weight:600;margin-bottom:8px">每天看一次的主界面</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.7">'
        '显示当前宏观环境评分、AI 市场判断、买入推荐列表、板块强弱热力图，'
        '以及全部 25 只 ETF 的综合排名。点击「刷新分析」按钮触发完整分析流程，约 20-30 秒完成。'
        '</div></div>'
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;padding:20px 22px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:8px">因子分析</div>'
        '<div style="color:#2C3A4A;font-weight:600;margin-bottom:8px">深入了解某只 ETF 为什么得这个分</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.7">'
        '选择任意一只 ETF，查看它在动量、量能、趋势、基本面四个因子上的详细数据，'
        '以及瀑布图（直观显示每个因子对最终评分的贡献量），还有 120 日价格走势图。'
        '</div></div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;'
        'padding:20px 22px;margin-bottom:12px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:8px">决策中心</div>'
        '<div style="color:#2C3A4A;font-weight:600;margin-bottom:8px">不同意 AI 的建议？在这里修改</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.7">'
        '提供三层人工干预机制：调整各因子的权重比例、修改某只 ETF 的单项因子分、'
        '直接覆盖最终买卖信号。所有修改都有记录。'
        '</div></div>'
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;padding:20px 22px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:8px">策略回测</div>'
        '<div style="color:#2C3A4A;font-weight:600;margin-bottom:8px">验证这套策略在历史上表现如何</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.7">'
        '选择时间段和参数，系统模拟用这套评分策略在历史上每周/每月调仓的结果，'
        '输出年化收益率、最大回撤、夏普比率等指标，与沪深300基准对比。'
        '历史回测不代表未来收益。'
        '</div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════
# 3. 七个评分因子
# ══════════════════════════════════════════
st.subheader("综合评分的 7 个因子")
st.markdown("系统给每只 ETF 打一个 **0-100 分**的综合分，由 7 个维度加权合成。默认权重如下，可在「决策中心」侧边栏自由调整。")

factors = [
    ("宏观环境", "20%", "分析整体经济大环境是否有利于股市上涨。", [
        ("PMI（采购经理人指数）",
         "调查全国制造业企业最近生意怎么样。超过 50 = 经济扩张，低于 50 = 收缩。就像体检时的体温，50 是正常线。"),
        ("CPI（消费者价格指数）",
         "衡量通货膨胀。1-3% 最理想：太低说明大家不花钱（通缩），太高说明钱不值钱（通胀），央行会加息压制股市。"),
        ("10 年国债收益率",
         "国家借钱的利率。利率低 = 钱便宜 = 企业容易融资 = 股市受益。利率高 = 资金从股市流向债券。"),
        ("上证 20 日涨跌幅",
         "市场整体短期趋势，简单直观。"),
    ]),
    ("板块轮动", "15%", "不同行业轮流表现好，就像季节一样循环。经济复苏时先是金融消费，再科技，再周期性行业。", [
        ("相对强度评分",
         "计算每个板块 ETF 相对于沪深 300 的超额收益。比如半导体 ETF 最近 20 天比大盘多涨 8%，说明资金正在流入，处于领先阶段。"),
    ]),
    ("价格动量", "20%", "核心逻辑：涨势中的股票更容易继续涨（趋势惯性）。", [
        ("20 日 / 60 日收益率",
         "这只 ETF 最近 1 个月、3 个月涨了多少？涨得越多，动量分越高。"),
        ("RSI（相对强弱指数）",
         "0-100 之间的数值。超过 70 = 过热可能回调，低于 30 = 超卖可能反弹。"),
    ]),
    ("成交量能", "15%", "核心逻辑：价格上涨同时成交量放大，才是真正的买盘，否则可能是虚涨。", [
        ("量比",
         "今天成交量除以过去 20 天平均成交量。量比大于 1.5 说明今天有资金明显进场。"),
        ("OBV（能量潮）",
         "累计计算每天上涨日成交量减去下跌日成交量，反映资金是在悄悄流入还是流出。"),
    ]),
    ("趋势强度", "15%", "判断这只 ETF 当前是否处于明确的趋势通道中，还是在无方向地横盘震荡。", [
        ("EMA 均线（指数移动平均线）",
         "价格的平滑曲线。价格站上 20 日均线和 60 日均线 = 短期、中期都是上涨趋势，系统加分。"),
        ("ADX（趋势强度）",
         "只判断趋势强不强，不管方向。ADX 大于 25 说明趋势明确，小于 15 说明横盘震荡没有方向。"),
        ("布林带位置",
         "价格在上下两条波动轨道中的位置。靠近下轨 = 相对低位，有潜在反弹空间，系统认为值得关注。"),
    ]),
    ("基本面", "10%", "衡量这只 ETF 自身的质量，与宏观和技术无关。", [
        ("年化波动率",
         "价格波动有多剧烈？波动越小，风险越低，系统给分越高（体现稳健偏好）。"),
        ("价格年内位置",
         "当前价格在今年最高价和最低价之间的位置。靠近年内低点，潜在涨幅更大。"),
        ("溢价折价率",
         "ETF 市价与它持有资产净值相比是贵了还是便宜了。折价时相当于打折买入，是好事。"),
    ]),
    ("市场情绪", "5%", "AI 读取当天财经新闻，判断市场对各板块的看法，转化为 0-100 的情绪分。", [
        ("新闻情绪分析",
         "需配置 Groq API Key 才能启用。AI 阅读最新财经新闻，输出各板块的情绪评分。未配置时默认 50 分（中性）。"),
    ]),
]

for name, weight, desc, details in factors:
    with st.expander(f"{name}   —   默认权重 {weight}"):
        st.markdown(f"<p style='color:#6B7280;margin-bottom:14px'>{desc}</p>", unsafe_allow_html=True)
        for title, explanation in details:
            st.markdown(
                f'<div style="display:flex;gap:12px;margin-bottom:10px;padding:10px 14px;'
                f'background:#F7F8FA;border-radius:6px;border-left:3px solid #7B9EC7">'
                f'<div><div style="color:#2C3A4A;font-weight:600;font-size:0.88rem;margin-bottom:3px">{title}</div>'
                f'<div style="color:#6B7280;font-size:0.85rem;line-height:1.65">{explanation}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

st.divider()

# ══════════════════════════════════════════
# 4. AI 的角色
# ══════════════════════════════════════════
st.subheader("AI 在系统中的两个角色")
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;padding:20px 22px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:10px">角色一：新闻分析师</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.75">'
        '批量阅读当天财经新闻（来自东方财富、新浪财经），输出：<br><br>'
        '· 整体市场情绪评分（-1 极度悲观 ~ +1 极度乐观）<br>'
        '· 各板块受影响程度和方向<br>'
        '· 主要风险因素（最多 5 条）<br>'
        '· 主要利好催化剂（最多 5 条）'
        '</div></div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<div style="background:white;border:1px solid #DDE4EE;border-radius:10px;padding:20px 22px">'
        '<div style="color:#7B9EC7;font-weight:700;font-size:0.8rem;letter-spacing:0.06em;margin-bottom:10px">角色二：综合协调者</div>'
        '<div style="color:#6B7280;font-size:0.88rem;line-height:1.75">'
        '看完所有量化分数后，写一段投资总结，并对个别 ETF 做微调：<br><br>'
        '· 生成 3-4 句市场综合判断<br>'
        '· 解释排名前几位 ETF 的逻辑<br>'
        '· 提示当前主要风险<br>'
        '· 对量化评分做微调（幅度上限 10 分）<br><br>'
        '<span style="color:#9B6B6B;font-size:0.82rem">'
        '重要：量化模型是主要判断依据，AI 只补充质性分析，不能单独左右结果。'
        '</span></div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════
# 5. 三层人工干预
# ══════════════════════════════════════════
st.subheader("三层人工干预机制")
st.markdown("系统设计理念：**量化为主、人工为辅**。你随时可以介入，所有介入都有记录。")

interventions = [
    ("第一层", "调整因子权重", "决策中心 → 左侧边栏",
     "用滑块调整 7 个因子各自占综合分的比例，分数实时重算，无需重新分析。",
     "你认为当前宏观比技术指标更重要，把宏观权重从 20% 拖到 40%，其他因子自动归一化。"),
    ("第二层", "修改单项因子分", "决策中心 → 点击 ETF 行 → 调整因子分",
     "对某只 ETF 的某个原始因子分进行微调，界面上会标注橙色提醒这项被人工修改过。",
     "你知道某只 ETF 即将分红但 akshare 数据还没更新，可以手动提高它的基本面分。"),
    ("第三层", "覆盖最终信号", "决策中心 → 点击 ETF 行 → 覆盖决策",
     "直接把 AI 建议的 BUY/HOLD/SELL 改为你认为正确的信号，但必须填写原因（不可为空）。",
     "AI 说 BUY，但你了解该行业最近有监管风险，改为 HOLD 并注明原因，系统记录时间戳。"),
]

for level, title, where, desc, example in interventions:
    st.markdown(
        f'<div style="display:flex;gap:16px;margin-bottom:12px;background:white;'
        f'border:1px solid #DDE4EE;border-radius:10px;padding:16px 20px">'
        f'<div style="min-width:52px;height:52px;background:#EEF3F8;border-radius:8px;'
        f'display:flex;align-items:center;justify-content:center;'
        f'color:#7B9EC7;font-weight:700;font-size:0.8rem;text-align:center;line-height:1.3">'
        f'{level}</div>'
        f'<div style="flex:1">'
        f'<div style="color:#2C3A4A;font-weight:600;margin-bottom:3px">{title}'
        f'<span style="color:#8A95A0;font-weight:400;font-size:0.82rem;margin-left:8px">{where}</span></div>'
        f'<div style="color:#6B7280;font-size:0.87rem;line-height:1.65;margin-bottom:6px">{desc}</div>'
        f'<div style="color:#9A8060;font-size:0.82rem;background:#F5F0E8;padding:6px 10px;border-radius:4px">'
        f'示例：{example}</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════
# 6. 买卖信号
# ══════════════════════════════════════════
st.subheader("买卖信号说明")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div style="background:white;border:1px solid #DDB8B8;border-radius:10px;padding:20px;text-align:center">'
        '<div style="background:#F5EDED;color:#9B6B6B;font-weight:700;font-size:0.9rem;'
        'padding:4px 16px;border-radius:4px;border:1px solid #DDB8B8;'
        'display:inline-block;margin-bottom:12px">BUY 买入</div>'
        '<div style="color:#2C3A4A;font-weight:700;font-size:1.4rem;margin-bottom:6px">综合分 &ge; 65</div>'
        '<div style="color:#6B7280;font-size:0.85rem;line-height:1.65">'
        '多个因子同时看好，系统认为该 ETF 当前值得建仓或加仓。分数越高，置信度越高。'
        '</div></div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<div style="background:white;border:1px solid #D4C4A8;border-radius:10px;padding:20px;text-align:center">'
        '<div style="background:#F5F0E8;color:#9A8060;font-weight:700;font-size:0.9rem;'
        'padding:4px 16px;border-radius:4px;border:1px solid #D4C4A8;'
        'display:inline-block;margin-bottom:12px">HOLD 持有</div>'
        '<div style="color:#2C3A4A;font-weight:700;font-size:1.4rem;margin-bottom:6px">40 &le; 综合分 &lt; 65</div>'
        '<div style="color:#6B7280;font-size:0.85rem;line-height:1.65">'
        '信号不够明确，建议继续观察。已持有的可以保留，未持有的不建议新买。'
        '</div></div>',
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        '<div style="background:white;border:1px solid #B3CCBB;border-radius:10px;padding:20px;text-align:center">'
        '<div style="background:#EDF2ED;color:#5E7F6A;font-weight:700;font-size:0.9rem;'
        'padding:4px 16px;border-radius:4px;border:1px solid #B3CCBB;'
        'display:inline-block;margin-bottom:12px">SELL 卖出</div>'
        '<div style="color:#2C3A4A;font-weight:700;font-size:1.4rem;margin-bottom:6px">综合分 &lt; 40</div>'
        '<div style="color:#6B7280;font-size:0.85rem;line-height:1.65">'
        '多个因子转弱，系统认为该 ETF 当前风险偏高，建议减仓或离场。'
        '</div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════
# 7. 回测指标
# ══════════════════════════════════════════
st.subheader("回测结果指标说明")

metrics = [
    ("年化收益率", "把策略总收益换算成每年平均赚多少百分比。比如 2 年赚了 44%，年化约 20%。"),
    ("超额收益", "策略年化收益率减去沪深300年化收益率。正数说明跑赢了大盘。"),
    ("夏普比率", "衡量每承担 1 单位风险能获得多少超额收益。大于 1 说明风险调整后收益不错，大于 2 说明很优秀。"),
    ("最大回撤", "从最高点到最低点的最大跌幅。比如 -25% 意味着某段时间内资产缩水了 25%。这是衡量最坏情况的指标。"),
    ("胜率", "所有交易日中，盈利日数量占总日数的比例。不是越高越好，要结合盈亏比看。"),
]

for name, explain in metrics:
    st.markdown(
        f'<div style="display:flex;gap:16px;padding:12px 16px;background:white;'
        f'border:1px solid #DDE4EE;border-radius:8px;margin-bottom:8px">'
        f'<div style="min-width:90px;color:#7B9EC7;font-weight:600;font-size:0.87rem;padding-top:1px">{name}</div>'
        f'<div style="color:#6B7280;font-size:0.87rem;line-height:1.65">{explain}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════
# 8. 免责声明
# ══════════════════════════════════════════
st.markdown(
    '<div style="background:#F5F0E8;border:1px solid #D4C4A8;border-left:4px solid #C4956A;'
    'border-radius:8px;padding:16px 20px;color:#6B5040;font-size:0.87rem;line-height:1.75">'
    '<strong>免责声明</strong><br><br>'
    '本系统是辅助决策工具，不构成任何投资建议。量化模型基于历史数据建立，'
    '无法预测政策突变、黑天鹅事件或市场非理性行为。'
    '回测结果不代表未来收益。ETF 投资存在本金损失风险。'
    '最终投资决策请结合自身风险承受能力和投资目标综合判断，必要时咨询专业投资顾问。'
    '</div>',
    unsafe_allow_html=True
)
