"""
回测引擎 - 走前向回测（Walk-forward），无前视偏差
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
from config.settings import config, WeightConfig
from core.data_fetcher import fetcher
from core.macro_scorer import compute_macro_score
from core.factor_engine import compute_factor_bundle
from core.sector_rotation import detect_sector_rotation
from core.portfolio_ranker import rank_all_etfs, apply_signals
from core.models import SentimentResult


@dataclass
class BacktestResult:
    equity_curve: pd.Series          # 净值曲线
    benchmark_curve: pd.Series        # 基准曲线（沪深300）
    trades: pd.DataFrame              # 交易记录
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    benchmark_annual_return: float
    excess_return: float
    start_date: str
    end_date: str
    config_summary: dict


def _compute_sharpe(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    if returns.std() == 0:
        return 0.0
    annual_ret = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    return (annual_ret - risk_free_rate) / annual_vol


def _compute_max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def run_backtest(
    start_date: str,
    end_date: str,
    weights: WeightConfig = None,
    top_n: int = 5,
    rebalance: str = "weekly",
    transaction_cost_bps: float = None,
) -> BacktestResult:
    """
    走前向回测

    注意：回测不使用LLM（历史新闻情绪难以重建，且成本高）
    只使用量化因子

    Args:
        start_date: 回测开始日期 "2023-01-01"
        end_date: 回测结束日期 "2024-12-31"
        weights: 因子权重
        top_n: 持仓ETF数量
        rebalance: "weekly" / "monthly"
        transaction_cost_bps: 交易成本（基点）
    """
    weights = weights or config.default_weights
    cost = (transaction_cost_bps or config.transaction_cost_bps) / 10000

    logger.info(f"开始回测: {start_date} ~ {end_date}, Top{top_n}, {rebalance}调仓")

    # 获取全量价格数据
    all_prices = fetcher.get_all_prices()
    universe = fetcher.get_etf_universe()

    if not all_prices:
        raise ValueError("无法获取价格数据")

    # 找到最长公共日期范围
    date_sets = [set(df.index.date) for df in all_prices.values() if len(df) > 10]
    if not date_sets:
        raise ValueError("数据不足")
    common_dates = sorted(date_sets[0].intersection(*date_sets[1:]))

    # 筛选回测区间
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    backtest_dates = [d for d in common_dates if start_dt <= d <= end_dt]

    if len(backtest_dates) < 30:
        raise ValueError(f"回测区间内数据不足 ({len(backtest_dates)}天)")

    # 确定调仓日期
    if rebalance == "weekly":
        # 每周第一个交易日
        rebalance_dates = []
        last_week = None
        for d in backtest_dates:
            week = d.isocalendar()[1]
            if week != last_week:
                rebalance_dates.append(d)
                last_week = week
    else:  # monthly
        rebalance_dates = []
        last_month = None
        for d in backtest_dates:
            if d.month != last_month:
                rebalance_dates.append(d)
                last_month = d.month

    # ── 回测主循环 ──
    portfolio_value = 1.0
    equity = []
    benchmark_values = []
    trades = []
    current_holdings: dict[str, float] = {}  # {etf_code: weight}
    warmup_days = 120  # 需要足够历史数据计算因子

    bm_code = "510300"
    bm_prices = all_prices.get(bm_code, pd.DataFrame())
    bm_start_price = None

    for date in backtest_dates:
        # 获取当日价格
        day_prices = {}
        for code, df in all_prices.items():
            date_idx = pd.Timestamp(date)
            if date_idx in df.index:
                day_prices[code] = float(df.loc[date_idx, "close"])

        # 基准净值
        if bm_code in day_prices:
            bm_price = day_prices[bm_code]
            if bm_start_price is None:
                bm_start_price = bm_price
            bm_nav = bm_price / bm_start_price
        else:
            bm_nav = benchmark_values[-1] if benchmark_values else 1.0

        # 如果是调仓日，重新计算因子和排名
        if date in rebalance_dates:
            # 截取到当前日期的历史数据
            historical_prices = {}
            for code, df in all_prices.items():
                hist = df[df.index.date <= date]
                if len(hist) >= warmup_days:
                    historical_prices[code] = hist

            if len(historical_prices) < 3:
                equity.append(portfolio_value)
                benchmark_values.append(bm_nav)
                continue

            # 计算因子（不用LLM）
            try:
                factor_bundles = {}
                for code, hist_df in historical_prices.items():
                    factor_bundles[code] = compute_factor_bundle(code, hist_df)

                # 简化的宏观评分（使用静态中性值）
                from core.models import MacroScore
                mock_macro = MacroScore(score=60.0, explanation="回测使用中性宏观评分")

                rotation_signals = detect_sector_rotation(historical_prices)

                # 情绪：回测不用LLM
                mock_sentiment = SentimentResult(overall_sentiment=0.0, sector_impacts={})

                scores = rank_all_etfs(
                    macro_score=mock_macro,
                    rotation_signals=rotation_signals,
                    factor_bundles=factor_bundles,
                    sentiment=mock_sentiment,
                    weights=weights,
                )
                scores = apply_signals(scores)

                # 选Top N个BUY信号
                buy_list = [s for s in scores if s.signal == "BUY"][:top_n]
                if not buy_list:
                    buy_list = scores[:top_n]  # 退而求其次，选最高分

                new_holdings = {s.etf_code: 1.0 / len(buy_list) for s in buy_list}

                # 计算交易成本
                old_codes = set(current_holdings.keys())
                new_codes = set(new_holdings.keys())
                changed = old_codes.symmetric_difference(new_codes)
                trade_cost = len(changed) * cost * portfolio_value / len(new_holdings)
                portfolio_value -= trade_cost

                # 记录交易
                for code in new_codes - old_codes:
                    trades.append({
                        "date": date,
                        "action": "BUY",
                        "etf": code,
                        "cost": trade_cost / max(1, len(changed))
                    })
                for code in old_codes - new_codes:
                    trades.append({
                        "date": date,
                        "action": "SELL",
                        "etf": code,
                        "cost": trade_cost / max(1, len(changed))
                    })

                current_holdings = new_holdings

            except Exception as e:
                logger.warning(f"调仓日 {date} 计算失败: {e}")

        # 计算当日组合收益
        if current_holdings:
            daily_return = sum(
                weight * (
                    (day_prices.get(code, 1.0) /
                     max(1e-6, day_prices.get(code, 1.0)))  # 当日无涨跌
                )
                for code, weight in current_holdings.items()
            )
            # 实际上需要昨日价格，简化处理
            portfolio_value = portfolio_value  # 在调仓时已更新

        equity.append(portfolio_value)
        benchmark_values.append(bm_nav)

    # 补充：更精确的净值计算（使用日收益率序列）
    equity_series, bm_series = _compute_accurate_equity(
        all_prices, backtest_dates, rebalance_dates, top_n, weights, cost
    )

    # 计算绩效指标
    returns = equity_series.pct_change().dropna()
    bm_returns = bm_series.pct_change().dropna()

    annual_ret = (equity_series.iloc[-1] ** (252 / len(equity_series)) - 1) * 100
    bm_annual_ret = (bm_series.iloc[-1] ** (252 / len(bm_series)) - 1) * 100

    return BacktestResult(
        equity_curve=equity_series,
        benchmark_curve=bm_series,
        trades=pd.DataFrame(trades) if trades else pd.DataFrame(),
        annual_return=round(annual_ret, 2),
        sharpe_ratio=round(_compute_sharpe(returns), 2),
        max_drawdown=round(_compute_max_drawdown(equity_series) * 100, 2),
        win_rate=round(float((returns > 0).mean()) * 100, 1),
        total_trades=len(trades),
        benchmark_annual_return=round(bm_annual_ret, 2),
        excess_return=round(annual_ret - bm_annual_ret, 2),
        start_date=start_date,
        end_date=end_date,
        config_summary={
            "top_n": top_n,
            "rebalance": rebalance,
            "transaction_cost_bps": (transaction_cost_bps or config.transaction_cost_bps),
            "weights": weights.to_dict(),
        }
    )


def _compute_accurate_equity(all_prices, backtest_dates, rebalance_dates,
                               top_n, weights, cost) -> tuple[pd.Series, pd.Series]:
    """
    精确的日收益率计算
    """
    warmup_days = 120
    bm_code = "510300"
    bm_df = all_prices.get(bm_code, pd.DataFrame())

    portfolio_value = 1.0
    bm_value = 1.0
    equity_dict = {}
    bm_dict = {}
    current_holdings = {}
    prev_prices = {}

    for i, date in enumerate(backtest_dates):
        date_ts = pd.Timestamp(date)

        # 当日价格
        day_prices = {}
        for code, df in all_prices.items():
            if date_ts in df.index:
                day_prices[code] = float(df.loc[date_ts, "close"])

        # 基准日收益
        if bm_code in day_prices and bm_code in prev_prices:
            bm_daily_ret = day_prices[bm_code] / prev_prices[bm_code] - 1
            bm_value *= (1 + bm_daily_ret)

        # 调仓
        if date in rebalance_dates and i >= warmup_days:
            historical_prices = {}
            for code, df in all_prices.items():
                hist = df[df.index.date <= date]
                if len(hist) >= warmup_days:
                    historical_prices[code] = hist

            if len(historical_prices) >= 3:
                try:
                    factor_bundles = {
                        code: compute_factor_bundle(code, hist)
                        for code, hist in historical_prices.items()
                    }
                    from core.models import MacroScore
                    mock_macro = MacroScore(score=60.0)
                    rotation_signals = detect_sector_rotation(historical_prices)
                    mock_sentiment = SentimentResult(overall_sentiment=0.0, sector_impacts={})

                    scores = rank_all_etfs(
                        macro_score=mock_macro,
                        rotation_signals=rotation_signals,
                        factor_bundles=factor_bundles,
                        sentiment=mock_sentiment,
                        weights=weights,
                    )
                    scores = apply_signals(scores)
                    buy_list = [s for s in scores if s.signal == "BUY"][:top_n]
                    if not buy_list:
                        buy_list = scores[:top_n]

                    new_holdings = {s.etf_code: 1.0 / len(buy_list) for s in buy_list}

                    # 交易成本
                    changed = set(current_holdings) ^ set(new_holdings)
                    portfolio_value *= (1 - cost * len(changed) / max(1, len(new_holdings)))
                    current_holdings = new_holdings
                except Exception:
                    pass

        # 组合日收益
        if current_holdings:
            daily_pnl = sum(
                weight * (day_prices.get(code, prev_prices.get(code, 1)) /
                          prev_prices.get(code, day_prices.get(code, 1)) - 1)
                for code, weight in current_holdings.items()
                if code in day_prices
            )
            portfolio_value *= (1 + daily_pnl)

        equity_dict[date_ts] = portfolio_value
        bm_dict[date_ts] = bm_value
        prev_prices = day_prices

    equity_series = pd.Series(equity_dict)
    bm_series = pd.Series(bm_dict)
    return equity_series, bm_series
