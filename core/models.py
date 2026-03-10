"""共享数据模型 - 每个分析模块的输出结构"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubScore(BaseModel):
    value: float
    score: float  # 0-100
    signal: str   # "positive" / "neutral" / "negative" / "expanding" / etc.
    description: str = ""


class MacroScore(BaseModel):
    score: float  # 0-100
    sub_scores: dict[str, SubScore] = {}
    explanation: str = ""
    updated_at: datetime = Field(default_factory=datetime.now)


class RotationSignal(BaseModel):
    sector: str
    score: float       # 0-100, relative strength
    momentum_20d: float
    momentum_60d: float
    signal: str        # "leading" / "lagging" / "neutral"
    description: str = ""


class FactorBundle(BaseModel):
    etf_code: str
    momentum: float     # 0-100
    volume: float       # 0-100
    trend: float        # 0-100
    fundamental: float  # 0-100
    momentum_detail: dict = {}
    volume_detail: dict = {}
    trend_detail: dict = {}
    fundamental_detail: dict = {}
    updated_at: datetime = Field(default_factory=datetime.now)


class SentimentResult(BaseModel):
    overall_sentiment: float         # -1 to +1
    sector_impacts: dict[str, dict]  # {sector: {score: float, reasoning: str}}
    key_risks: list[str] = []
    key_catalysts: list[str] = []
    confidence: float = 0.5
    raw_news_count: int = 0
    updated_at: datetime = Field(default_factory=datetime.now)


class CompositeScore(BaseModel):
    etf_code: str
    etf_name: str = ""
    sector: str = ""
    composite_score: float   # 0-100
    rank: int = 0
    breakdown: dict[str, float] = {}  # {factor: weighted_contribution}
    raw_scores: dict[str, float] = {}  # {factor: raw_score_0_to_100}
    claude_adjustment: float = 0.0
    signal: str = "HOLD"  # "BUY" / "HOLD" / "SELL"
    confidence: float = 0.5
    updated_at: datetime = Field(default_factory=datetime.now)


class OrchestratorResult(BaseModel):
    executive_summary: str = ""
    top_picks_rationale: dict[str, str] = {}  # {etf_code: rationale}
    key_risks: list[str] = []
    confidence_adjustments: dict[str, float] = {}  # {etf_code: delta}
    override_commentary: str = ""
    updated_at: datetime = Field(default_factory=datetime.now)


class PipelineState(BaseModel):
    macro_score: Optional[MacroScore] = None
    rotation_signals: dict[str, RotationSignal] = {}
    factor_bundles: dict[str, FactorBundle] = {}
    sentiment: Optional[SentimentResult] = None
    composite_scores: list[CompositeScore] = []
    orchestrator: Optional[OrchestratorResult] = None
    refreshed_at: datetime = Field(default_factory=datetime.now)
    errors: list[str] = []
