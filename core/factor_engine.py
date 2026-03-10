"""
多因子打分引擎 - 计算每只ETF的4个量化因子
动量(Momentum) + 成交量(Volume) + 趋势(Trend) + 基本面(Fundamental)
"""
import numpy as np
import pandas as pd
from loguru import logger
from core.models import FactorBundle
from core.data_fetcher import fetcher


def _safe_float(val, default=50.0) -> float:
    try:
        v = float(val)
        return v if np.isfinite(v) else default
    except Exception:
        return default


def _normalize_to_100(series: pd.Series) -> pd.Series:
    """将序列标准化到 0-100"""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return (series - mn) / (mx - mn) * 100


def _score_momentum(df: pd.DataFrame) -> tuple[float, dict]:
    """
    动量因子 (0-100)
    - 20日收益率 (40%)
    - 60日收益率 (30%)
    - RSI(14) (30%)
    """
    if len(df) < 61:
        return 50.0, {}

    close = df["close"]

    # 收益率
    ret_20 = _safe_float(close.pct_change(20).iloc[-1] * 100)
    ret_60 = _safe_float(close.pct_change(60).iloc[-1] * 100) if len(df) >= 61 else 0.0

    # RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = _safe_float(100 - 100 / (1 + rs.iloc[-1]))

    # 评分
    def score_return(r):
        if r > 10: return 90
        elif r > 5: return 75
        elif r > 0: return 60
        elif r > -5: return 40
        elif r > -10: return 25
        else: return 10

    s20 = score_return(ret_20)
    s60 = score_return(ret_60)
    s_rsi = min(100, max(0, rsi))  # RSI 本身就是 0-100

    total = 0.4 * s20 + 0.3 * s60 + 0.3 * s_rsi

    return round(total, 1), {
        "ret_20d": round(ret_20, 2),
        "ret_60d": round(ret_60, 2),
        "rsi_14": round(rsi, 1),
        "score_ret20": s20,
        "score_ret60": s60,
        "score_rsi": round(s_rsi, 1),
    }


def _score_volume(df: pd.DataFrame) -> tuple[float, dict]:
    """
    成交量因子 (0-100)
    - 量比（当前成交量 / 20日均量）(50%)
    - OBV 趋势 (50%)
    """
    if len(df) < 21 or "volume" not in df.columns:
        return 50.0, {}

    vol = df["volume"]
    close = df["close"]

    # 量比
    avg_vol_20 = vol.rolling(20).mean().iloc[-1]
    cur_vol = vol.iloc[-1]
    vol_ratio = _safe_float(cur_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0)

    def score_vol_ratio(r):
        if r > 2.5: return 85
        elif r > 1.5: return 75
        elif r > 1.0: return 60
        elif r > 0.7: return 45
        else: return 30

    # OBV 趋势（5日OBV相对20日OBV）
    obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
    obv_5 = obv.rolling(5).mean().iloc[-1]
    obv_20 = obv.rolling(20).mean().iloc[-1]
    obv_trend = _safe_float((obv_5 - obv_20) / (abs(obv_20) + 1e-10) * 100)

    def score_obv(t):
        if t > 5: return 80
        elif t > 0: return 65
        elif t > -5: return 45
        else: return 25

    s_vol = score_vol_ratio(vol_ratio)
    s_obv = score_obv(obv_trend)
    total = 0.5 * s_vol + 0.5 * s_obv

    return round(total, 1), {
        "vol_ratio": round(vol_ratio, 2),
        "obv_trend_pct": round(obv_trend, 2),
        "score_vol_ratio": s_vol,
        "score_obv": s_obv,
    }


def _score_trend(df: pd.DataFrame) -> tuple[float, dict]:
    """
    趋势因子 (0-100)
    - 价格 vs EMA20 / EMA60 位置 (40%)
    - ADX(14) 趋势强度 (30%)
    - 布林带位置 (30%)
    """
    if len(df) < 61:
        return 50.0, {}

    close = df["close"]

    # EMA
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema60 = close.ewm(span=60).mean().iloc[-1]
    price = close.iloc[-1]

    above_ema20 = price > ema20
    above_ema60 = price > ema60
    ema_score = (int(above_ema20) * 50 + int(above_ema60) * 50)

    # ADX (简化版)
    high = df["high"] if "high" in df.columns else close * 1.001
    low = df["low"] if "low" in df.columns else close * 0.999
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()

    dm_plus = (high.diff()).clip(lower=0)
    dm_minus = (-low.diff()).clip(lower=0)
    di_plus = (dm_plus.rolling(14).mean() / atr14.replace(0, np.nan) * 100).fillna(0)
    di_minus = (dm_minus.rolling(14).mean() / atr14.replace(0, np.nan) * 100).fillna(0)
    dx = ((di_plus - di_minus).abs() / (di_plus + di_minus + 1e-10) * 100)
    adx = _safe_float(dx.rolling(14).mean().iloc[-1])

    def score_adx(a):
        if a > 40: return 90  # 强趋势
        elif a > 25: return 70  # 趋势明确
        elif a > 15: return 50  # 弱趋势
        else: return 30  # 无趋势/震荡

    # 布林带位置
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_range = (bb_upper - bb_lower).iloc[-1]
    bb_pos = _safe_float((price - bb_lower.iloc[-1]) / (bb_range + 1e-10) * 100)
    bb_pos = max(0, min(100, bb_pos))

    s_ema = ema_score
    s_adx = score_adx(adx)
    s_bb = bb_pos

    total = 0.4 * s_ema + 0.3 * s_adx + 0.3 * s_bb

    return round(total, 1), {
        "above_ema20": above_ema20,
        "above_ema60": above_ema60,
        "adx": round(adx, 1),
        "bb_position_pct": round(bb_pos, 1),
        "score_ema": s_ema,
        "score_adx": s_adx,
        "score_bb": round(s_bb, 1),
    }


def _score_fundamental(df: pd.DataFrame, etf_code: str) -> tuple[float, dict]:
    """
    基本面因子 (0-100)
    - 波动率（越低越好）(40%)
    - 价格相对年内高低点位置 (30%)
    - 溢价折价率 (30%)
    """
    if len(df) < 20:
        return 50.0, {}

    close = df["close"]

    # 年化波动率
    daily_ret = close.pct_change().dropna()
    vol_ann = _safe_float(daily_ret.tail(60).std() * np.sqrt(252) * 100)

    def score_volatility(v):
        if v < 10: return 85
        elif v < 15: return 75
        elif v < 20: return 60
        elif v < 30: return 45
        else: return 25

    # 价格在年内高低点的位置
    year_high = close.tail(252).max()
    year_low = close.tail(252).min()
    price = close.iloc[-1]
    price_pos = _safe_float((price - year_low) / (year_high - year_low + 1e-10) * 100)
    price_pos = max(0, min(100, price_pos))

    # 溢价折价率（从数据源获取，简化处理）
    premium = 0.0  # 默认无溢折价
    try:
        premium = fetcher.get_etf_premium_discount(etf_code)
    except Exception:
        pass

    def score_premium(p):
        if -0.2 <= p <= 0.2: return 80   # 接近净值
        elif -0.5 <= p <= 0.5: return 65
        elif -1.0 <= p <= 1.0: return 50
        elif p > 1.0: return 35  # 高溢价可能回归
        else: return 40  # 折价

    s_vol = score_volatility(vol_ann)
    s_price = price_pos  # 价格在年内中低位 = 更有潜力
    # 价格低位加分（买低不买高的逻辑）
    s_price_adj = 100 - s_price  # 价格越低分越高（均值回归）
    s_prem = score_premium(premium)

    total = 0.4 * s_vol + 0.3 * s_price_adj + 0.3 * s_prem

    return round(total, 1), {
        "annual_volatility_pct": round(vol_ann, 1),
        "price_position_pct": round(price_pos, 1),
        "premium_discount_pct": round(premium, 2),
        "score_volatility": s_vol,
        "score_price_position": round(s_price_adj, 1),
        "score_premium": s_prem,
    }


def compute_factor_bundle(etf_code: str, df: pd.DataFrame = None) -> FactorBundle:
    """计算单只ETF的全部因子"""
    if df is None:
        df = fetcher.get_price_history(etf_code)

    if len(df) < 20:
        logger.warning(f"{etf_code} 数据不足，返回中性因子")
        return FactorBundle(etf_code=etf_code,
                            momentum=50, volume=50, trend=50, fundamental=50)

    try:
        mom_score, mom_detail = _score_momentum(df)
        vol_score, vol_detail = _score_volume(df)
        trend_score, trend_detail = _score_trend(df)
        fund_score, fund_detail = _score_fundamental(df, etf_code)

        return FactorBundle(
            etf_code=etf_code,
            momentum=mom_score,
            volume=vol_score,
            trend=trend_score,
            fundamental=fund_score,
            momentum_detail=mom_detail,
            volume_detail=vol_detail,
            trend_detail=trend_detail,
            fundamental_detail=fund_detail,
        )

    except Exception as e:
        logger.error(f"因子计算失败 {etf_code}: {e}")
        return FactorBundle(etf_code=etf_code,
                            momentum=50, volume=50, trend=50, fundamental=50)


def compute_all_factors(price_data: dict[str, pd.DataFrame] = None) -> dict[str, FactorBundle]:
    """批量计算所有ETF因子"""
    if price_data is None:
        price_data = fetcher.get_all_prices()

    universe = fetcher.get_etf_universe()
    result = {}
    for etf in universe:
        code = etf["code"]
        df = price_data.get(code)
        result[code] = compute_factor_bundle(code, df)
        logger.debug(f"{code} 因子: 动量={result[code].momentum:.0f} "
                     f"量能={result[code].volume:.0f} "
                     f"趋势={result[code].trend:.0f} "
                     f"基本面={result[code].fundamental:.0f}")

    return result
