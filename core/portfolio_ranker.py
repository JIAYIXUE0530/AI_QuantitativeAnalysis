"""
组合打分与排名模块
整合所有因子 → 计算加权综合分 → 生成排名
"""
from loguru import logger
from config.settings import config, WeightConfig
from core.models import (
    CompositeScore, MacroScore, RotationSignal,
    FactorBundle, SentimentResult, OrchestratorResult
)
from core.data_fetcher import fetcher
from core.sector_rotation import get_etf_rotation_score
from core.llm_analyst import analyst


def compute_composite_score(
    etf_info: dict,
    macro_score: MacroScore,
    rotation_signals: dict[str, RotationSignal],
    factor_bundle: FactorBundle,
    sentiment: SentimentResult,
    weights: WeightConfig,
    score_overrides: dict = None,
    claude_adjustments: dict = None,
) -> CompositeScore:
    """
    计算单只ETF的综合评分

    公式:
    composite = w_macro * macro + w_rotation * rotation + w_momentum * momentum +
                w_volume * volume + w_trend * trend + w_fundamental * fundamental +
                w_sentiment * sentiment
    """
    code = etf_info["code"]
    sector = etf_info.get("sector", "宽基")

    # 原始分数
    raw_macro = macro_score.score if macro_score else 50.0
    raw_rotation = get_etf_rotation_score(code, sector, rotation_signals)
    raw_momentum = factor_bundle.momentum
    raw_volume = factor_bundle.volume
    raw_trend = factor_bundle.trend
    raw_fundamental = factor_bundle.fundamental
    raw_sentiment = analyst.get_sentiment_score_for_sector(sector, sentiment)

    # 应用人工score干预
    if score_overrides and code in score_overrides:
        overrides = score_overrides[code]
        raw_macro = overrides.get("macro", raw_macro)
        raw_rotation = overrides.get("rotation", raw_rotation)
        raw_momentum = overrides.get("momentum", raw_momentum)
        raw_volume = overrides.get("volume", raw_volume)
        raw_trend = overrides.get("trend", raw_trend)
        raw_fundamental = overrides.get("fundamental", raw_fundamental)
        raw_sentiment = overrides.get("sentiment", raw_sentiment)

    # 归一化权重
    w = weights.normalize()

    # 加权计算
    raw_composite = (
        w.macro * raw_macro +
        w.rotation * raw_rotation +
        w.momentum * raw_momentum +
        w.volume * raw_volume +
        w.trend * raw_trend +
        w.fundamental * raw_fundamental +
        w.sentiment * raw_sentiment
    )

    # Claude 调整（bounded ±10）
    claude_adj = 0.0
    if claude_adjustments and code in claude_adjustments:
        claude_adj = float(claude_adjustments[code])
        claude_adj = max(-config.llm_max_confidence_adjustment,
                         min(config.llm_max_confidence_adjustment, claude_adj))

    final_score = max(0, min(100, raw_composite + claude_adj))

    # 各因子对综合分的贡献
    breakdown = {
        "macro": round(w.macro * raw_macro, 1),
        "rotation": round(w.rotation * raw_rotation, 1),
        "momentum": round(w.momentum * raw_momentum, 1),
        "volume": round(w.volume * raw_volume, 1),
        "trend": round(w.trend * raw_trend, 1),
        "fundamental": round(w.fundamental * raw_fundamental, 1),
        "sentiment": round(w.sentiment * raw_sentiment, 1),
        "claude_adjustment": round(claude_adj, 1),
    }

    raw_scores = {
        "macro": round(raw_macro, 1),
        "rotation": round(raw_rotation, 1),
        "momentum": round(raw_momentum, 1),
        "volume": round(raw_volume, 1),
        "trend": round(raw_trend, 1),
        "fundamental": round(raw_fundamental, 1),
        "sentiment": round(raw_sentiment, 1),
    }

    return CompositeScore(
        etf_code=code,
        etf_name=etf_info.get("name", code),
        sector=sector,
        composite_score=round(final_score, 1),
        breakdown=breakdown,
        raw_scores=raw_scores,
        claude_adjustment=round(claude_adj, 1),
    )


def rank_all_etfs(
    macro_score: MacroScore,
    rotation_signals: dict[str, RotationSignal],
    factor_bundles: dict[str, FactorBundle],
    sentiment: SentimentResult,
    weights: WeightConfig = None,
    score_overrides: dict = None,
    claude_adjustments: dict = None,
) -> list[CompositeScore]:
    """
    对全部ETF打分排名，返回按综合分降序列表
    """
    if weights is None:
        weights = config.default_weights

    universe = fetcher.get_etf_universe()
    scores = []

    for etf_info in universe:
        code = etf_info["code"]
        bundle = factor_bundles.get(code)
        if bundle is None:
            from core.models import FactorBundle
            bundle = FactorBundle(etf_code=code, momentum=50, volume=50,
                                  trend=50, fundamental=50)

        score = compute_composite_score(
            etf_info=etf_info,
            macro_score=macro_score,
            rotation_signals=rotation_signals,
            factor_bundle=bundle,
            sentiment=sentiment,
            weights=weights,
            score_overrides=score_overrides,
            claude_adjustments=claude_adjustments,
        )
        scores.append(score)

    # 按综合分降序排列
    scores.sort(key=lambda x: x.composite_score, reverse=True)

    # 赋予排名
    for i, s in enumerate(scores):
        s.rank = i + 1

    logger.info(f"ETF排名完成: Top3 = "
                f"{scores[0].etf_code}({scores[0].composite_score:.0f}), "
                f"{scores[1].etf_code}({scores[1].composite_score:.0f}), "
                f"{scores[2].etf_code}({scores[2].composite_score:.0f})"
                if len(scores) >= 3 else "排名结果不足3只")

    return scores


def apply_signals(scores: list[CompositeScore],
                   buy_threshold: float = None,
                   sell_threshold: float = None,
                   decision_overrides: dict = None) -> list[CompositeScore]:
    """
    根据综合分生成买卖信号
    """
    buy_thresh = buy_threshold or config.buy_threshold
    sell_thresh = sell_threshold or config.sell_threshold

    for s in scores:
        # 人工决策干预优先
        if decision_overrides and s.etf_code in decision_overrides:
            override = decision_overrides[s.etf_code]
            s.signal = override.get("signal", s.signal)
            s.confidence = 1.0  # 人工干预，置信度设为100%
            continue

        if s.composite_score >= buy_thresh:
            s.signal = "BUY"
            s.confidence = min(1.0, (s.composite_score - buy_thresh) / (100 - buy_thresh) * 0.5 + 0.5)
        elif s.composite_score <= sell_thresh:
            s.signal = "SELL"
            s.confidence = min(1.0, (sell_thresh - s.composite_score) / sell_thresh * 0.5 + 0.5)
        else:
            s.signal = "HOLD"
            s.confidence = 0.5

    return scores
