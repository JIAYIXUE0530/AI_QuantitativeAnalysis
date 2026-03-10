"""
宏观打分模块 - 对政治经济环境进行综合评分
输出 0-100 分 + 子指标详情
"""
from loguru import logger
from core.models import MacroScore, SubScore
from core.data_fetcher import fetcher


def _score_pmi(pmi: float) -> tuple[float, str]:
    """PMI 评分: 50以上扩张，50以下收缩"""
    if pmi >= 52:
        return 85, "强力扩张"
    elif pmi >= 50.5:
        return 70, "温和扩张"
    elif pmi >= 50:
        return 55, "临界扩张"
    elif pmi >= 49:
        return 40, "轻微收缩"
    elif pmi >= 48:
        return 25, "明显收缩"
    else:
        return 10, "深度收缩"


def _score_cpi(cpi: float) -> tuple[float, str]:
    """CPI 评分: 适度通胀最佳（1-3%），通缩/通胀过热均差"""
    if 1.0 <= cpi <= 3.0:
        return 80, "通胀温和"
    elif 0 <= cpi < 1.0:
        return 55, "通胀偏低"
    elif cpi < 0:
        return 30, "通缩风险"
    elif 3.0 < cpi <= 4.0:
        return 50, "通胀偏高"
    else:
        return 20, "通胀过热"


def _score_bond_yield(yield_10y: float) -> tuple[float, str]:
    """10年期国债收益率: 低利率→宽松→利好权益"""
    if yield_10y < 2.0:
        return 90, "宽松货币环境"
    elif yield_10y < 2.5:
        return 75, "偏宽松"
    elif yield_10y < 3.0:
        return 60, "中性"
    elif yield_10y < 3.5:
        return 40, "偏紧"
    else:
        return 20, "紧缩环境"


def _score_market_trend(trend_20d: float) -> tuple[float, str]:
    """市场趋势评分（上证20日涨幅）"""
    if trend_20d > 8:
        return 90, "强势上涨"
    elif trend_20d > 3:
        return 75, "上涨趋势"
    elif trend_20d > -3:
        return 55, "震荡"
    elif trend_20d > -8:
        return 35, "下跌趋势"
    else:
        return 15, "大幅下跌"


def compute_macro_score() -> MacroScore:
    """
    计算宏观综合评分
    权重: PMI(30%) + CPI(20%) + 债券收益率(25%) + 市场趋势(25%)
    """
    try:
        indicators = fetcher.get_macro_indicators()

        pmi = indicators.get("pmi_manufacturing", 50.0)
        cpi = indicators.get("cpi_yoy", 2.0)
        yield_10y = indicators.get("bond_yield_10y", 2.5)
        sh_trend = indicators.get("sh_trend_20d", 0.0)

        pmi_score, pmi_signal = _score_pmi(pmi)
        cpi_score, cpi_signal = _score_cpi(cpi)
        yield_score, yield_signal = _score_bond_yield(yield_10y)
        trend_score, trend_signal = _score_market_trend(sh_trend)

        # 加权综合分
        composite = (
            0.30 * pmi_score +
            0.20 * cpi_score +
            0.25 * yield_score +
            0.25 * trend_score
        )

        # 生成解释
        explanations = []
        if pmi_score >= 70:
            explanations.append(f"PMI {pmi:.1f}，制造业{pmi_signal}")
        else:
            explanations.append(f"PMI {pmi:.1f}，制造业{pmi_signal}，需关注")
        if yield_score >= 70:
            explanations.append(f"利率环境{yield_signal}（{yield_10y:.2f}%），权益资产受益")
        if trend_score >= 70:
            explanations.append(f"市场{trend_signal}（20日+{sh_trend:.1f}%）")

        explanation = "；".join(explanations) + f"。宏观综合评分 {composite:.0f}/100。"

        return MacroScore(
            score=round(composite, 1),
            sub_scores={
                "pmi": SubScore(value=pmi, score=pmi_score, signal=pmi_signal,
                                description="制造业PMI"),
                "cpi": SubScore(value=cpi, score=cpi_score, signal=cpi_signal,
                                description="CPI同比"),
                "bond_yield": SubScore(value=yield_10y, score=yield_score, signal=yield_signal,
                                       description="10年国债收益率(%)"),
                "market_trend": SubScore(value=sh_trend, score=trend_score, signal=trend_signal,
                                         description="上证20日涨跌幅(%)"),
            },
            explanation=explanation,
        )

    except Exception as e:
        logger.error(f"宏观评分计算失败: {e}")
        return MacroScore(
            score=50.0,
            explanation=f"宏观数据获取异常，使用中性评分。错误: {e}",
        )
