"""
决策中心 - 人机协同决策页，三层干预机制
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
from core.models import CompositeScore
from ui.components.override_manager import (
    save_weights, save_score_override, clear_score_override,
    save_decision_override, clear_decision_override
)

from ui.style import THINKCELL_CSS

st.set_page_config(page_title="决策中心", layout="wide", page_icon="🎯")
st.markdown(THINKCELL_CSS, unsafe_allow_html=True)

for key, default in [
    ("pipeline_state", None),
    ("custom_weights", config.default_weights.to_dict()),
    ("score_overrides", {}),
    ("decision_overrides", {}),
    ("last_refresh", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.title("🎯 决策中心")
st.caption("量化模型为主，人工干预为辅。所有干预均有记录。")

# ═══════════════════════════════════════════════════════════════
# 侧边栏：权重控制（Level 1 干预）
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("因子权重调整")
    st.caption("调整各因子在综合评分中的权重比例")

    weights_raw = st.session_state.custom_weights
    factor_config = [
        ("macro", "宏观环境", "PMI、利率、市场趋势"),
        ("rotation", "板块轮动", "相对强弱、轮动信号"),
        ("momentum", "价格动量", "20/60日收益率、RSI"),
        ("volume", "成交量能", "量比、OBV趋势"),
        ("trend", "趋势强度", "EMA、ADX、布林带"),
        ("fundamental", "基本面", "波动率、估值位置"),
        ("sentiment", "市场情绪", "Claude新闻分析"),
    ]

    new_weights = {}
    for key, label, desc in factor_config:
        val = weights_raw.get(key, 0.15)
        new_val = st.slider(
            label,
            min_value=0.0,
            max_value=1.0,
            value=float(val),
            step=0.05,
            help=desc,
            key=f"weight_{key}",
        )
        new_weights[key] = new_val

    # 归一化显示
    total = sum(new_weights.values())
    if total > 0:
        normalized = {k: round(v / total, 3) for k, v in new_weights.items()}
        st.caption(f"权重总和: {total:.2f} → 自动归一化")
    else:
        normalized = new_weights

    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("保存权重", use_container_width=True):
            st.session_state.custom_weights = new_weights
            save_weights(new_weights)
            st.success("已保存")
    with col_reset:
        if st.button("重置默认", use_container_width=True):
            st.session_state.custom_weights = config.default_weights.to_dict()
            save_weights(config.default_weights.to_dict())
            st.rerun()

    st.divider()

    # 快速重新计算（不调LLM，仅重算分数）
    if st.button("用新权重重新计算", type="primary", use_container_width=True):
        with st.spinner("重新计算中..."):
            state = run_full_pipeline(
                weights=WeightConfig(**new_weights),
                score_overrides=st.session_state.score_overrides,
                decision_overrides=st.session_state.decision_overrides,
                skip_llm=True,  # 只重算量化分，不再调LLM
            )
        st.session_state.pipeline_state = state
        st.session_state.custom_weights = new_weights
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    if st.button("完整分析（含AI）", use_container_width=True):
        with st.spinner("AI分析中，约15-30秒..."):
            state = run_full_pipeline(
                weights=WeightConfig(**new_weights),
                score_overrides=st.session_state.score_overrides,
                decision_overrides=st.session_state.decision_overrides,
                skip_llm=False,
            )
        st.session_state.pipeline_state = state
        st.session_state.custom_weights = new_weights
        st.session_state.last_refresh = datetime.now()
        st.rerun()

    st.divider()
    # 干预统计
    n_score = sum(1 for k, v in st.session_state.score_overrides.items()
                  if any(f != "_updated_at" for f in v))
    n_decision = len(st.session_state.decision_overrides)
    st.metric("因子分数干预", f"{n_score} 只ETF")
    st.metric("决策信号干预", f"{n_decision} 只ETF")

    if n_decision > 0 and st.button("清除所有决策干预", use_container_width=True):
        for code in list(st.session_state.decision_overrides.keys()):
            clear_decision_override(code)
        st.session_state.decision_overrides = {}
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# 主内容
# ═══════════════════════════════════════════════════════════════
state = st.session_state.pipeline_state
if state is None:
    st.warning("请先在「总览仪表盘」执行一次完整分析")
    st.stop()

# ── Claude 综合分析 ──
if state.orchestrator:
    orch = state.orchestrator
    st.markdown(f"""
    <div class="claude-card">
    <b>Claude AI 综合判断</b><br>
    {orch.executive_summary}
    </div>
    """, unsafe_allow_html=True)

    if orch.override_commentary:
        st.info(f"AI对人工干预的评论: {orch.override_commentary}")

# ── 决策表格（带内联干预）──
st.divider()
st.subheader("ETF评分与决策表")
st.caption("""
**操作说明**:
- 点击 [调整因子分] 可对某ETF的原始因子分进行微调（Level 2 干预）
- 点击 [覆盖决策] 可将AI信号改为你的判断，需填写原因（Level 3 干预）
- 橙色 ⚠️ 表示已存在人工干预
""")

scores = state.composite_scores
if not scores:
    st.warning("暂无分析结果")
    st.stop()

# 过滤
signal_filter = st.multiselect(
    "筛选信号", ["BUY", "HOLD", "SELL"], default=["BUY", "HOLD", "SELL"]
)
scores_filtered = [s for s in scores if s.signal in signal_filter]

for s in scores_filtered:
    is_decision_override = s.etf_code in st.session_state.decision_overrides
    is_score_override = s.etf_code in st.session_state.score_overrides
    has_override = is_decision_override or is_score_override

    signal_color = {"BUY": "#E84B4B", "SELL": "#2DB84B", "HOLD": "#F0A500"}
    color = signal_color.get(s.signal, "#888")

    with st.expander(
        f"{'⚠️ ' if has_override else ''}#{s.rank} {s.etf_name} ({s.etf_code}) "
        f"— 综合 {s.composite_score:.1f}分 "
        f"— {'🔴' if s.signal == 'BUY' else ('🟢' if s.signal == 'SELL' else '🟡')} {s.signal}",
        expanded=(s.rank <= 5)
    ):
        main_col, action_col = st.columns([3, 2])

        with main_col:
            # 各因子分展示
            factor_labels = {
                "macro": "宏观", "rotation": "轮动",
                "momentum": "动量", "volume": "量能",
                "trend": "趋势", "fundamental": "基本面", "sentiment": "情绪"
            }
            cols = st.columns(7)
            for i, (factor, label) in enumerate(factor_labels.items()):
                raw = s.raw_scores.get(factor, 0)
                is_factor_override = (
                    s.etf_code in st.session_state.score_overrides and
                    factor in st.session_state.score_overrides.get(s.etf_code, {})
                )
                with cols[i]:
                    if is_factor_override:
                        st.markdown(
                            f"<div class='factor-override'><small>{label}</small><br>"
                            f"<b style='color:#F0A500'>{raw:.0f}</b>⚙️</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<small>{label}</small><br><b>{raw:.0f}</b>",
                            unsafe_allow_html=True
                        )

            # Claude 调整
            if s.claude_adjustment != 0:
                st.caption(f"Claude调整: {s.claude_adjustment:+.1f}分")

            # 决策干预记录
            if is_decision_override:
                override_info = st.session_state.decision_overrides[s.etf_code]
                st.markdown(
                    f"<span class='override-badge'>人工干预</span> "
                    f"→ **{override_info['signal']}** | "
                    f"原因: {override_info['reason']} | "
                    f"时间: {override_info.get('created_at', '')[:16]}",
                    unsafe_allow_html=True
                )

        with action_col:
            # Level 2: 因子分数干预
            with st.popover("调整因子分", use_container_width=True):
                st.markdown(f"**调整 {s.etf_name} 的因子分**")
                st.caption("修改后将影响综合评分计算（橙色标注）")

                override_factor = st.selectbox(
                    "选择因子",
                    options=list(factor_labels.keys()),
                    format_func=lambda x: factor_labels[x],
                    key=f"factor_sel_{s.etf_code}"
                )
                current_val = s.raw_scores.get(override_factor, 50)
                new_val = st.number_input(
                    f"新分数 (当前: {current_val:.0f})",
                    min_value=0.0, max_value=100.0,
                    value=float(current_val),
                    step=1.0,
                    key=f"factor_val_{s.etf_code}_{override_factor}"
                )
                reason_score = st.text_input(
                    "调整原因",
                    key=f"score_reason_{s.etf_code}"
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("确认调整", key=f"score_apply_{s.etf_code}",
                                  type="primary", use_container_width=True):
                        save_score_override(s.etf_code, override_factor, new_val)
                        if s.etf_code not in st.session_state.score_overrides:
                            st.session_state.score_overrides[s.etf_code] = {}
                        st.session_state.score_overrides[s.etf_code][override_factor] = new_val
                        st.success("已保存，请重新计算")
                with c2:
                    if st.button("清除干预", key=f"score_clear_{s.etf_code}",
                                  use_container_width=True):
                        clear_score_override(s.etf_code)
                        st.session_state.score_overrides.pop(s.etf_code, None)
                        st.success("已清除")
                        st.rerun()

            # Level 3: 决策信号干预
            with st.popover("覆盖决策", use_container_width=True):
                st.markdown(f"**覆盖 {s.etf_name} 的投资决策**")
                st.warning(f"当前AI决策: **{s.signal}** ({s.composite_score:.1f}分)")

                new_signal = st.selectbox(
                    "新决策",
                    options=["BUY", "HOLD", "SELL"],
                    index=["BUY", "HOLD", "SELL"].index(s.signal),
                    key=f"new_signal_{s.etf_code}"
                )
                override_reason = st.text_area(
                    "干预原因（必填）",
                    placeholder="例如：政策风险未被量化模型捕捉...",
                    key=f"override_reason_{s.etf_code}"
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "确认覆盖",
                        key=f"decision_apply_{s.etf_code}",
                        type="primary",
                        use_container_width=True,
                        disabled=not override_reason
                    ):
                        save_decision_override(s.etf_code, new_signal, override_reason)
                        st.session_state.decision_overrides[s.etf_code] = {
                            "signal": new_signal,
                            "reason": override_reason,
                            "created_at": datetime.now().isoformat(),
                        }
                        st.success(f"已覆盖为 {new_signal}")
                        st.rerun()
                with c2:
                    if is_decision_override:
                        if st.button("取消干预", key=f"decision_clear_{s.etf_code}",
                                      use_container_width=True):
                            clear_decision_override(s.etf_code)
                            st.session_state.decision_overrides.pop(s.etf_code, None)
                            st.rerun()

# ── 导出 ──
st.divider()
st.subheader("导出决策")

if scores:
    rows = []
    for s in scores:
        override = st.session_state.decision_overrides.get(s.etf_code, {})
        rows.append({
            "代码": s.etf_code,
            "名称": s.etf_name,
            "板块": s.sector,
            "综合评分": s.composite_score,
            "排名": s.rank,
            "AI信号": s.signal,
            "是否人工干预": "是" if s.etf_code in st.session_state.decision_overrides else "否",
            "干预原因": override.get("reason", ""),
            "分析时间": state.refreshed_at.strftime("%Y-%m-%d %H:%M"),
        })
    df = pd.DataFrame(rows)
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "下载决策报告 (CSV)",
        data=csv,
        file_name=f"ETF决策_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
