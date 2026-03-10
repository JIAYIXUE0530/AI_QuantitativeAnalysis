"""
数据获取层 - 封装所有 akshare 调用，带本地 Parquet 缓存
"""
import json
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from config.settings import config


class ETFDataFetcher:
    def __init__(self):
        self.cache_dir = config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._universe: list[dict] = config.load_etf_universe()

    # ──────────────────────────────────────────────
    # 缓存工具
    # ──────────────────────────────────────────────
    def _cache_path(self, key: str) -> Path:
        safe = hashlib.md5(key.encode()).hexdigest()[:12]
        return self.cache_dir / f"{safe}.parquet"

    def _cache_meta_path(self, key: str) -> Path:
        safe = hashlib.md5(key.encode()).hexdigest()[:12]
        return self.cache_dir / f"{safe}.meta.json"

    def _is_cache_fresh(self, key: str, ttl_hours: int = None) -> bool:
        ttl = ttl_hours or config.cache_ttl_hours
        meta_path = self._cache_meta_path(key)
        if not meta_path.exists():
            return False
        with open(meta_path) as f:
            meta = json.load(f)
        saved_at = datetime.fromisoformat(meta["saved_at"])
        return datetime.now() - saved_at < timedelta(hours=ttl)

    def _save_cache(self, key: str, df: pd.DataFrame):
        cache_path = self._cache_path(key)
        df.to_parquet(cache_path, index=True)
        with open(self._cache_meta_path(key), "w") as f:
            json.dump({"saved_at": datetime.now().isoformat(), "key": key}, f)

    def _load_cache(self, key: str) -> pd.DataFrame:
        return pd.read_parquet(self._cache_path(key))

    # ──────────────────────────────────────────────
    # ETF 基础信息
    # ──────────────────────────────────────────────
    def get_etf_universe(self) -> list[dict]:
        return self._universe

    def get_etf_info(self, etf_code: str) -> dict:
        for etf in self._universe:
            if etf["code"] == etf_code:
                return etf
        return {"code": etf_code, "name": etf_code, "sector": "未知", "asset_class": "股票"}

    # ──────────────────────────────────────────────
    # 价格历史
    # ──────────────────────────────────────────────
    def get_price_history(self, etf_code: str, days: int = None) -> pd.DataFrame:
        days = days or config.price_history_days
        cache_key = f"price_{etf_code}_{days}"

        if self._is_cache_fresh(cache_key):
            return self._load_cache(cache_key)

        try:
            import akshare as ak
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days + 60)).strftime("%Y%m%d")

            df = ak.fund_etf_hist_em(
                symbol=etf_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            # 标准化列名
            rename_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "amount", "振幅": "amplitude",
                "涨跌幅": "pct_change", "涨跌额": "change",
                "换手率": "turnover"
            }
            df = df.rename(columns=rename_map)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()

            self._save_cache(cache_key, df)
            logger.info(f"已获取 {etf_code} 价格数据 {len(df)} 条")
            return df

        except Exception as e:
            logger.error(f"获取 {etf_code} 价格数据失败: {e}")
            # 返回模拟数据（开发/测试用）
            return self._mock_price_data(etf_code, days)

    def get_all_prices(self) -> dict[str, pd.DataFrame]:
        """批量获取所有ETF价格，用于因子计算"""
        result = {}
        for etf in self._universe:
            code = etf["code"]
            try:
                result[code] = self.get_price_history(code)
            except Exception as e:
                logger.warning(f"跳过 {code}: {e}")
        return result

    # ──────────────────────────────────────────────
    # 宏观指标
    # ──────────────────────────────────────────────
    def get_macro_indicators(self) -> dict:
        cache_key = "macro_indicators"
        if self._is_cache_fresh(cache_key, ttl_hours=24):
            df = self._load_cache(cache_key)
            return df.to_dict(orient="index")

        try:
            import akshare as ak
            indicators = {}

            # PMI 制造业
            try:
                pmi_df = ak.macro_china_pmi_yearly()
                latest_pmi = float(pmi_df.iloc[-1]["制造业-指数"]) if "制造业-指数" in pmi_df.columns else 50.0
                indicators["pmi_manufacturing"] = latest_pmi
            except Exception:
                indicators["pmi_manufacturing"] = 50.0

            # CPI
            try:
                cpi_df = ak.macro_china_cpi_monthly()
                latest_cpi = float(cpi_df.iloc[-1].iloc[1]) if len(cpi_df) > 0 else 2.0
                indicators["cpi_yoy"] = latest_cpi
            except Exception:
                indicators["cpi_yoy"] = 2.0

            # 10年期国债收益率（货币政策宽松度代理）
            try:
                bond_df = ak.bond_china_yield(start_date="20230101",
                                               end_date=datetime.now().strftime("%Y%m%d"))
                if len(bond_df) > 0:
                    indicators["bond_yield_10y"] = float(bond_df.iloc[-1].get("10年", 2.5))
                else:
                    indicators["bond_yield_10y"] = 2.5
            except Exception:
                indicators["bond_yield_10y"] = 2.5

            # 上证指数趋势
            try:
                sh_df = ak.stock_zh_index_daily(symbol="sh000001")
                sh_df["pct_20d"] = sh_df["close"].pct_change(20)
                indicators["sh_trend_20d"] = float(sh_df.iloc[-1]["pct_20d"]) * 100
            except Exception:
                indicators["sh_trend_20d"] = 0.0

            logger.info(f"宏观指标获取成功: {list(indicators.keys())}")
            # 保存为单行 DataFrame
            result_df = pd.DataFrame([indicators])
            result_df.index = [datetime.now().strftime("%Y-%m-%d")]
            self._save_cache(cache_key, result_df)
            return indicators

        except Exception as e:
            logger.error(f"获取宏观指标失败: {e}")
            return {
                "pmi_manufacturing": 50.0,
                "cpi_yoy": 2.0,
                "bond_yield_10y": 2.5,
                "sh_trend_20d": 0.0,
            }

    # ──────────────────────────────────────────────
    # 新闻数据
    # ──────────────────────────────────────────────
    def get_news_batch(self, keywords: list[str] = None) -> list[dict]:
        cache_key = f"news_{datetime.now().strftime('%Y%m%d_%H')}"
        if self._is_cache_fresh(cache_key, ttl_hours=4):
            df = self._load_cache(cache_key)
            return df.to_dict(orient="records")

        news_items = []
        try:
            import akshare as ak
            import concurrent.futures

            def _fetch_em_news():
                """东方财富快讯（速度快，无分页）"""
                try:
                    # stock_news_em 对单股快速，对市场新闻会翻页很慢
                    # 改用 news_cctv 或 stock_news_em 固定symbol避免大量请求
                    df = ak.stock_news_em(symbol="000001")
                    items = []
                    for _, row in df.head(20).iterrows():
                        title = str(row.get("新闻标题", row.get("title", "")))
                        if title and title != "nan":
                            items.append({
                                "title": title,
                                "content": str(row.get("新闻内容", row.get("content", "")))[:300],
                                "time": str(row.get("发布时间", row.get("time", ""))),
                                "source": "东方财富"
                            })
                    return items
                except Exception as e:
                    logger.warning(f"东方财富新闻: {e}")
                    return []

            def _fetch_sina_news():
                """新浪财经头条（通常很快）"""
                try:
                    df = ak.stock_news_sina()
                    items = []
                    for _, row in df.head(15).iterrows():
                        title = str(row.iloc[0]) if len(row) > 0 else ""
                        if title and title != "nan":
                            items.append({
                                "title": title,
                                "content": str(row.iloc[1])[:300] if len(row) > 1 else "",
                                "time": str(row.iloc[-1]) if len(row) > 0 else "",
                                "source": "新浪财经"
                            })
                    return items
                except Exception as e:
                    logger.warning(f"新浪新闻: {e}")
                    return []

            # 并行抓取，各自最多等10秒
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(_fetch_em_news)
                f2 = executor.submit(_fetch_sina_news)
                for f in concurrent.futures.as_completed([f1, f2], timeout=15):
                    try:
                        news_items.extend(f.result())
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"新闻获取失败: {e}")

        if not news_items:
            # 模拟新闻（开发用）
            news_items = self._mock_news()

        # 去重 + 截取
        seen = set()
        unique_news = []
        for item in news_items:
            if item["title"] not in seen:
                seen.add(item["title"])
                unique_news.append(item)

        unique_news = unique_news[:config.max_news_per_batch]
        df = pd.DataFrame(unique_news)
        self._save_cache(cache_key, df)
        logger.info(f"获取新闻 {len(unique_news)} 条")
        return unique_news

    # ──────────────────────────────────────────────
    # 板块资金流向
    # ──────────────────────────────────────────────
    def get_sector_fund_flow(self) -> pd.DataFrame:
        cache_key = f"sector_flow_{datetime.now().strftime('%Y%m%d')}"
        if self._is_cache_fresh(cache_key, ttl_hours=6):
            return self._load_cache(cache_key)

        try:
            import akshare as ak
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
            df.columns = [c.lower() for c in df.columns]
            self._save_cache(cache_key, df)
            return df
        except Exception as e:
            logger.warning(f"板块资金流向获取失败: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────────
    # ETF 溢价折价率（基本面）
    # ──────────────────────────────────────────────
    def get_etf_premium_discount(self, etf_code: str) -> float:
        """返回溢价率 %，正数为溢价，负数为折价"""
        try:
            import akshare as ak
            df = ak.fund_etf_premium_discount_sina(symbol=etf_code)
            if len(df) > 0:
                return float(df.iloc[-1].get("溢价率", 0))
        except Exception:
            pass
        return 0.0

    # ──────────────────────────────────────────────
    # 模拟数据（akshare 不可用时的后备）
    # ──────────────────────────────────────────────
    def _mock_price_data(self, etf_code: str, days: int) -> pd.DataFrame:
        logger.warning(f"使用 {etf_code} 的模拟价格数据")
        dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
        np.random.seed(hash(etf_code) % 2**31)
        prices = 1.0 + np.random.randn(days).cumsum() * 0.01
        prices = np.abs(prices) + 0.5
        return pd.DataFrame({
            "open": prices * 0.999,
            "close": prices,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "volume": np.random.randint(1000000, 50000000, days).astype(float),
            "amount": np.random.randint(10000000, 500000000, days).astype(float),
            "pct_change": np.random.randn(days) * 1.0,
        }, index=dates)

    def _mock_news(self) -> list[dict]:
        return [
            {"title": "央行维持LPR不变，市场流动性保持合理充裕", "content": "...", "time": "2026-03-09", "source": "新华社"},
            {"title": "两会政策利好科技板块，半导体及AI方向获政策支持", "content": "...", "time": "2026-03-09", "source": "人民日报"},
            {"title": "新能源汽车销量持续增长，带动产业链整体向好", "content": "...", "time": "2026-03-09", "source": "证券时报"},
            {"title": "消费复苏力度不及预期，食品饮料板块承压", "content": "...", "time": "2026-03-08", "source": "第一财经"},
            {"title": "美联储降息预期推动黄金价格走强", "content": "...", "time": "2026-03-08", "source": "财联社"},
        ]


# 单例
fetcher = ETFDataFetcher()
