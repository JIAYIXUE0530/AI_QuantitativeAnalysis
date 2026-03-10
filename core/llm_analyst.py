"""
LLM 分析模块
支持多个提供商:
  - groq      (免费, 推荐: llama-3.3-70b-versatile)
  - anthropic (付费 API，有 Claude Pro 不等于有 API)
  - none      (禁用LLM，纯量化模式)
"""
import json
from datetime import datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import config
from core.models import SentimentResult, OrchestratorResult, PipelineState


# ────────────────────────────────────────────────────
# JSON 输出 schemas（Groq/Anthropic 通用）
# ────────────────────────────────────────────────────

NEWS_ANALYSIS_SCHEMA = {
    "overall_sentiment": "number (-1到+1，-1极度悲观，+1极度乐观)",
    "sector_impacts": {
        "<板块名>": {
            "score": "number (0-100)",
            "direction": "string (positive/neutral/negative)",
            "reasoning": "string"
        }
    },
    "key_risks": ["string (最多5条)"],
    "key_catalysts": ["string (最多5条)"],
    "confidence": "number (0-1)"
}

ORCHESTRATOR_SCHEMA = {
    "executive_summary": "string (3-4句综合判断)",
    "top_picks_rationale": {"<etf_code>": "string (投资逻辑)"},
    "key_risks": ["string (2-3条主要风险)"],
    "confidence_adjustments": {"<etf_code>": "number (±10以内的评分微调)"},
    "override_commentary": "string (对人工干预的评论，无则空字符串)"
}


def _build_client():
    """根据配置构建LLM客户端"""
    if config.llm_provider == "groq":
        try:
            from groq import Groq
            return ("groq", Groq(api_key=config.groq_api_key))
        except ImportError:
            logger.error("groq 包未安装，请运行: pip install groq")
            return (None, None)
    elif config.llm_provider == "anthropic":
        try:
            import anthropic
            return ("anthropic", anthropic.Anthropic(api_key=config.anthropic_api_key))
        except ImportError:
            logger.error("anthropic 包未安装")
            return (None, None)
    return (None, None)


class LLMAnalyst:
    def __init__(self):
        self._provider, self._client = _build_client()
        self._news_cache: dict = {}
        self._news_cache_time: datetime = None

        if self._provider and config.llm_enabled:
            logger.info(f"LLM已启用: {config.llm_provider} "
                        f"({'模型: ' + config.groq_model if self._provider == 'groq' else 'claude'})")
        else:
            logger.warning("LLM未配置，将使用纯量化模式（不影响核心量化功能）")

    def is_available(self) -> bool:
        return self._client is not None and config.llm_enabled

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_llm(self, system: str, user: str, schema: dict) -> dict:
        """统一调用接口，强制返回JSON"""
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        full_user = (
            f"{user}\n\n"
            f"请严格按照以下JSON格式返回，不要有任何额外文字：\n{schema_str}"
        )

        if self._provider == "groq":
            response = self._client.chat.completions.create(
                model=config.groq_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": full_user},
                ],
                temperature=0.3,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content

        elif self._provider == "anthropic":
            response = self._client.messages.create(
                model=config.claude_model,
                max_tokens=3000,
                system=system + "\n必须以纯JSON格式回复，不要包含markdown代码块。",
                messages=[{"role": "user", "content": full_user}],
            )
            raw = response.content[0].text
        else:
            return {}

        # 解析JSON（处理模型可能的 markdown 包裹）
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}，尝试提取...")
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise

    # ────────────────────────────────────────────────────
    # Mode A: 新闻情绪分析
    # ────────────────────────────────────────────────────
    def analyze_news(self, news_items: list[dict]) -> SentimentResult:
        if not news_items:
            return SentimentResult(overall_sentiment=0.0, sector_impacts={},
                                    key_risks=["暂无新闻数据"], key_catalysts=[])

        if not self.is_available():
            logger.info("LLM未启用，跳过新闻情绪分析")
            return SentimentResult(overall_sentiment=0.0, sector_impacts={},
                                    key_risks=["配置GROQ_API_KEY以启用AI情绪分析"],
                                    key_catalysts=[], raw_news_count=len(news_items))

        # 同批新闻4小时内不重复分析
        cache_key = str(hash(str([n.get("title", "") for n in news_items[:5]])))
        if (self._news_cache_time and
                (datetime.now() - self._news_cache_time).seconds < 4 * 3600 and
                cache_key in self._news_cache):
            return self._news_cache[cache_key]

        news_text = "\n".join([
            f"[{i+1}] {item.get('time', '')} | {item.get('source', '')} | "
            f"{item.get('title', '')}。{item.get('content', '')[:150]}"
            for i, item in enumerate(news_items[:config.max_news_per_batch])
        ])

        system = (
            "你是专业A股量化投资分析师，善于从财经新闻中提取市场情绪信号。"
            "分析要客观数据化，聚焦对ETF投资的实际影响。"
            f"今天日期：{datetime.now().strftime('%Y年%m月%d日')}"
        )
        user = (
            f"分析以下{len(news_items)}条A股财经新闻的市场情绪：\n\n{news_text}\n\n"
            "板块范围：科技、半导体、新能源、新能源汽车、医疗、金融、消费、军工、传媒、能源、宽基、债券、黄金。"
        )

        try:
            result = self._call_llm(system, user, NEWS_ANALYSIS_SCHEMA)
            sentiment = SentimentResult(
                overall_sentiment=float(result.get("overall_sentiment", 0)),
                sector_impacts=result.get("sector_impacts", {}),
                key_risks=result.get("key_risks", []),
                key_catalysts=result.get("key_catalysts", []),
                confidence=float(result.get("confidence", 0.5)),
                raw_news_count=len(news_items),
            )
            self._news_cache[cache_key] = sentiment
            self._news_cache_time = datetime.now()
            logger.info(f"新闻情绪分析完成: {sentiment.overall_sentiment:+.2f}")
            return sentiment

        except Exception as e:
            logger.error(f"新闻情绪分析失败: {e}")
            return SentimentResult(overall_sentiment=0.0, sector_impacts={},
                                    key_risks=[f"LLM分析异常: {str(e)[:80]}"],
                                    key_catalysts=[], raw_news_count=len(news_items))

    # ────────────────────────────────────────────────────
    # Mode B: 投资决策综合协调者
    # ────────────────────────────────────────────────────
    def synthesize_investment_view(self,
                                    pipeline_state: PipelineState,
                                    human_overrides: dict = None) -> OrchestratorResult:
        if not self.is_available():
            return OrchestratorResult(
                executive_summary=(
                    "当前为纯量化模式（未配置LLM）。"
                    "量化排名结果可直接使用。"
                    "如需AI综合解读，请在 .env 中配置 GROQ_API_KEY（免费）。"
                )
            )

        macro = pipeline_state.macro_score
        macro_text = f"宏观评分 {macro.score:.0f}/100 — {macro.explanation}" if macro else "N/A"

        leading = [s for s, r in pipeline_state.rotation_signals.items() if r.signal == "leading"]
        lagging = [s for s, r in pipeline_state.rotation_signals.items() if r.signal == "lagging"]
        rotation_text = f"领先板块: {', '.join(leading[:3]) or '无'}；滞后: {', '.join(lagging[:3]) or '无'}"

        sent = pipeline_state.sentiment
        sentiment_text = (f"情绪 {sent.overall_sentiment:+.2f}，"
                          f"风险: {'; '.join(sent.key_risks[:2])}，"
                          f"催化: {'; '.join(sent.key_catalysts[:2])}"
                          if sent else "N/A")

        top10 = "\n".join([
            f"#{s.rank} {s.etf_code}({s.etf_name}) 综合{s.composite_score:.0f}分 "
            f"[宏观{s.raw_scores.get('macro', 0):.0f} 动量{s.raw_scores.get('momentum', 0):.0f} "
            f"趋势{s.raw_scores.get('trend', 0):.0f} 情绪{s.raw_scores.get('sentiment', 0):.0f}] → {s.signal}"
            for s in pipeline_state.composite_scores[:10]
        ])

        override_text = ""
        if human_overrides:
            override_text = "\n人工干预: " + "; ".join([
                f"{k}→{v.get('signal')}({v.get('reason', '')})"
                for k, v in human_overrides.items()
            ])

        system = (
            "你是TRAE量化投资系统的AI分析师。"
            "基于量化模型输出给出综合投资建议，评分调整必须在±10分以内。"
            "用专业简洁的中文回复。"
        )
        user = (
            f"【宏观】{macro_text}\n"
            f"【板块轮动】{rotation_text}\n"
            f"【市场情绪】{sentiment_text}\n"
            f"【ETF量化排名前10】\n{top10}"
            f"{override_text}"
        )

        try:
            result = self._call_llm(system, user, ORCHESTRATOR_SCHEMA)
            adjustments = {
                k: max(-config.llm_max_confidence_adjustment,
                       min(config.llm_max_confidence_adjustment, float(v)))
                for k, v in result.get("confidence_adjustments", {}).items()
            }
            orch = OrchestratorResult(
                executive_summary=result.get("executive_summary", ""),
                top_picks_rationale=result.get("top_picks_rationale", {}),
                key_risks=result.get("key_risks", []),
                confidence_adjustments=adjustments,
                override_commentary=result.get("override_commentary", ""),
            )
            logger.info(f"AI综合判断完成: {orch.executive_summary[:60]}...")
            return orch

        except Exception as e:
            logger.error(f"AI综合分析失败: {e}")
            return OrchestratorResult(
                executive_summary=f"AI综合分析暂时不可用（{str(e)[:80]}），请依据量化评分决策。"
            )

    def get_sentiment_score_for_sector(self, sector: str,
                                        sentiment: SentimentResult) -> float:
        if not sentiment or not sentiment.sector_impacts:
            return 50.0
        if sector in sentiment.sector_impacts:
            return min(100, max(0, float(sentiment.sector_impacts[sector].get("score", 50))))
        for key, impact in sentiment.sector_impacts.items():
            if key in sector or sector in key:
                return min(100, max(0, float(impact.get("score", 50))))
        return 50 + sentiment.overall_sentiment * 30


# 单例
analyst = LLMAnalyst()
