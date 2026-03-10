import os
import json
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent


class WeightConfig(BaseModel):
    macro: float = Field(0.20, ge=0, le=1)
    rotation: float = Field(0.15, ge=0, le=1)
    momentum: float = Field(0.20, ge=0, le=1)
    volume: float = Field(0.15, ge=0, le=1)
    trend: float = Field(0.15, ge=0, le=1)
    fundamental: float = Field(0.10, ge=0, le=1)
    sentiment: float = Field(0.05, ge=0, le=1)

    def normalize(self) -> "WeightConfig":
        total = sum([self.macro, self.rotation, self.momentum,
                     self.volume, self.trend, self.fundamental, self.sentiment])
        if total == 0:
            return WeightConfig()
        return WeightConfig(
            macro=self.macro / total,
            rotation=self.rotation / total,
            momentum=self.momentum / total,
            volume=self.volume / total,
            trend=self.trend / total,
            fundamental=self.fundamental / total,
            sentiment=self.sentiment / total,
        )

    def to_dict(self) -> dict:
        return {
            "macro": self.macro,
            "rotation": self.rotation,
            "momentum": self.momentum,
            "volume": self.volume,
            "trend": self.trend,
            "fundamental": self.fundamental,
            "sentiment": self.sentiment,
        }


class SystemConfig(BaseModel):
    # Paths
    base_dir: Path = BASE_DIR
    etf_universe_path: Path = BASE_DIR / "config" / "etf_universe.json"
    cache_dir: Path = BASE_DIR / "data" / "cache"
    overrides_dir: Path = BASE_DIR / "data" / "overrides"
    backtest_dir: Path = BASE_DIR / "data" / "backtest"
    logs_dir: Path = BASE_DIR / "logs"

    # Data settings
    cache_ttl_hours: int = 4
    price_history_days: int = 252
    news_lookback_hours: int = 48

    # LLM 提供商: "groq"（免费）| "anthropic"（需付费API）| "none"（禁用）
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq"))
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = "llama-3.3-70b-versatile"  # 免费，效果最好
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    claude_model: str = "claude-sonnet-4-6"
    max_news_per_batch: int = 20
    llm_cache_hours: int = 4
    llm_max_confidence_adjustment: float = 10.0

    @property
    def llm_enabled(self) -> bool:
        if self.llm_provider == "groq":
            return bool(self.groq_api_key)
        elif self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False

    # Signal thresholds
    buy_threshold: float = 65.0
    sell_threshold: float = 40.0

    # Default weights
    default_weights: WeightConfig = Field(default_factory=WeightConfig)

    # Backtest
    transaction_cost_bps: float = 10.0
    default_top_n: int = 5

    class Config:
        arbitrary_types_allowed = True

    def load_etf_universe(self) -> list[dict]:
        with open(self.etf_universe_path) as f:
            return json.load(f)


# Singleton
config = SystemConfig()
