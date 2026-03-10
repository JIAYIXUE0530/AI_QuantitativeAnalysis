"""
板块轮动检测 - 计算各板块的相对强弱和轮动信号
"""
import pandas as pd
import numpy as np
from loguru import logger
from core.models import RotationSignal
from core.data_fetcher import fetcher


# 板块 → ETF代码 映射（取板块代表性ETF）
SECTOR_ETF_MAP = {
    "科技": "588000",
    "半导体": "512480",
    "新能源": "515790",
    "新能源汽车": "516160",
    "医疗": "512010",
    "金融": "512800",
    "消费": "159928",
    "军工": "512660",
    "传媒": "159869",
    "能源": "515220",
    "宽基": "510300",
}


def compute_relative_strength(price_data: dict[str, pd.DataFrame],
                               benchmark_code: str = "510300",
                               lookback: int = 60) -> dict[str, float]:
    """
    计算各ETF相对基准（沪深300）的相对强度
    RS = ETF收益率 / 基准收益率，归一化到0-100
    """
    if benchmark_code not in price_data:
        return {}

    bm = price_data[benchmark_code]
    if len(bm) < lookback:
        return {}

    bm_ret = bm["close"].pct_change(lookback).iloc[-1]

    rs_scores = {}
    for code, df in price_data.items():
        if len(df) < lookback:
            continue
        etf_ret = df["close"].pct_change(lookback).iloc[-1]
        rs = float(etf_ret) - float(bm_ret)  # 超额收益
        rs_scores[code] = rs

    # 归一化到0-100
    if not rs_scores:
        return {}
    values = list(rs_scores.values())
    mn, mx = min(values), max(values)
    if mx == mn:
        return {k: 50.0 for k in rs_scores}

    return {k: round((v - mn) / (mx - mn) * 100, 1) for k, v in rs_scores.items()}


def detect_sector_rotation(price_data: dict[str, pd.DataFrame] = None) -> dict[str, RotationSignal]:
    """
    检测板块轮动信号
    - 计算各板块代表性ETF的20日/60日相对强度
    - 判断轮动阶段: leading(领先) / neutral(中性) / lagging(滞后)
    """
    if price_data is None:
        price_data = fetcher.get_all_prices()

    rs_20 = compute_relative_strength(price_data, lookback=20)
    rs_60 = compute_relative_strength(price_data, lookback=60)

    signals = {}
    for sector, etf_code in SECTOR_ETF_MAP.items():
        if etf_code not in price_data:
            continue

        df = price_data[etf_code]
        if len(df) < 20:
            continue

        score_20 = rs_20.get(etf_code, 50.0)
        score_60 = rs_60.get(etf_code, 50.0)

        # 综合分：近期动量 60% + 中期动量 40%
        composite = 0.6 * score_20 + 0.4 * score_60

        # 判断轮动阶段
        if composite >= 70:
            signal = "leading"
            description = f"板块领先市场，近期相对强度高（{composite:.0f}分）"
        elif composite >= 45:
            signal = "neutral"
            description = f"板块与市场同步（{composite:.0f}分）"
        else:
            signal = "lagging"
            description = f"板块落后市场，相对强度弱（{composite:.0f}分）"

        # 获取实际收益率
        try:
            close = df["close"]
            mom_20 = float(close.pct_change(20).iloc[-1] * 100)
            mom_60 = float(close.pct_change(min(60, len(close) - 1)).iloc[-1] * 100)
        except Exception:
            mom_20, mom_60 = 0.0, 0.0

        signals[sector] = RotationSignal(
            sector=sector,
            score=round(composite, 1),
            momentum_20d=round(mom_20, 2),
            momentum_60d=round(mom_60, 2),
            signal=signal,
            description=description,
        )

    logger.info(f"板块轮动信号计算完成: {len(signals)} 个板块")
    return signals


def get_etf_rotation_score(etf_code: str,
                            sector: str,
                            rotation_signals: dict[str, RotationSignal]) -> float:
    """
    获取某ETF所属板块的轮动评分
    用于组合打分时赋予板块因子权重
    """
    if sector in rotation_signals:
        return rotation_signals[sector].score
    # 如果找不到直接板块，看是否有相关板块
    for s, signal in rotation_signals.items():
        if s in sector or sector in s:
            return signal.score
    return 50.0  # 中性
