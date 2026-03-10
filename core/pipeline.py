"""
主分析流水线 - 整合所有模块，一次完整的分析流程
"""
from datetime import datetime
from loguru import logger
from config.settings import config, WeightConfig
from core.models import PipelineState
from core.data_fetcher import fetcher
from core.macro_scorer import compute_macro_score
from core.factor_engine import compute_all_factors
from core.sector_rotation import detect_sector_rotation
from core.llm_analyst import analyst
from core.portfolio_ranker import rank_all_etfs, apply_signals


def run_full_pipeline(
    weights: WeightConfig = None,
    score_overrides: dict = None,
    decision_overrides: dict = None,
    skip_llm: bool = False,
    progress_callback=None,
) -> PipelineState:
    """
    执行完整分析流水线

    Args:
        weights: 因子权重配置（可由UI传入）
        score_overrides: 人工因子分数干预 {etf_code: {factor: score}}
        decision_overrides: 人工决策干预 {etf_code: {signal, reason}}
        skip_llm: 跳过LLM分析（用于快速回测或离线测试）
        progress_callback: 进度回调 (step: str, pct: float) → None
    """
    state = PipelineState()
    weights = weights or config.default_weights

    def progress(msg: str, pct: float):
        logger.info(f"[{pct:.0f}%] {msg}")
        if progress_callback:
            progress_callback(msg, pct)

    try:
        # Step 1: 获取所有价格数据
        progress("正在获取ETF历史价格数据...", 5)
        price_data = fetcher.get_all_prices()

        # Step 2: 宏观评分
        progress("计算宏观环境评分...", 20)
        state.macro_score = compute_macro_score()

        # Step 3: 板块轮动
        progress("检测板块轮动信号...", 35)
        state.rotation_signals = detect_sector_rotation(price_data)

        # Step 4: 多因子计算
        progress("计算多因子评分...", 50)
        state.factor_bundles = compute_all_factors(price_data)

        # Step 5: LLM 新闻分析
        if not skip_llm:
            progress("AI正在分析市场新闻...", 65)
            news = fetcher.get_news_batch()
            state.sentiment = analyst.analyze_news(news)
        else:
            from core.models import SentimentResult
            state.sentiment = SentimentResult(overall_sentiment=0.0, sector_impacts={})

        # Step 6: 组合排名
        progress("计算综合评分与排名...", 80)
        state.composite_scores = rank_all_etfs(
            macro_score=state.macro_score,
            rotation_signals=state.rotation_signals,
            factor_bundles=state.factor_bundles,
            sentiment=state.sentiment,
            weights=weights,
            score_overrides=score_overrides,
            claude_adjustments=None,  # 先不加，等orchestrator结果
        )

        # Step 7: LLM 综合协调
        if not skip_llm:
            progress("AI综合研判与决策建议...", 90)
            human_overrides = decision_overrides or {}
            state.orchestrator = analyst.synthesize_investment_view(state, human_overrides)

            # 用 Claude 的调整重新计算分数
            if state.orchestrator.confidence_adjustments:
                state.composite_scores = rank_all_etfs(
                    macro_score=state.macro_score,
                    rotation_signals=state.rotation_signals,
                    factor_bundles=state.factor_bundles,
                    sentiment=state.sentiment,
                    weights=weights,
                    score_overrides=score_overrides,
                    claude_adjustments=state.orchestrator.confidence_adjustments,
                )

        # Step 8: 生成信号
        progress("生成买卖信号...", 95)
        state.composite_scores = apply_signals(
            state.composite_scores,
            decision_overrides=decision_overrides,
        )

        state.refreshed_at = datetime.now()
        progress("分析完成！", 100)
        logger.success(f"流水线运行完成，分析 {len(state.composite_scores)} 只ETF")

    except Exception as e:
        logger.error(f"流水线运行异常: {e}")
        state.errors.append(str(e))

    return state
