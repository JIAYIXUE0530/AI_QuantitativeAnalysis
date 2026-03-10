"""
人工干预管理器 - 三层干预系统的持久化和读取
"""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from config.settings import config


WEIGHTS_FILE = config.overrides_dir / "weights.json"
SCORE_OVERRIDES_FILE = config.overrides_dir / "score_adjustments.json"
DECISION_OVERRIDES_FILE = config.overrides_dir / "decisions.json"


def _ensure_dir():
    config.overrides_dir.mkdir(parents=True, exist_ok=True)


# ────────────────────────────────────────────────────
# 权重管理（Level 1）
# ────────────────────────────────────────────────────

def load_weights() -> dict:
    _ensure_dir()
    if WEIGHTS_FILE.exists():
        with open(WEIGHTS_FILE) as f:
            return json.load(f)
    return config.default_weights.to_dict()


def save_weights(weights_dict: dict):
    _ensure_dir()
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights_dict, f, ensure_ascii=False, indent=2)
    logger.info(f"权重已保存: {weights_dict}")


# ────────────────────────────────────────────────────
# 因子分数干预（Level 2）
# ────────────────────────────────────────────────────

def load_score_overrides() -> dict:
    _ensure_dir()
    if SCORE_OVERRIDES_FILE.exists():
        with open(SCORE_OVERRIDES_FILE) as f:
            return json.load(f)
    return {}


def save_score_override(etf_code: str, factor: str, new_score: float):
    _ensure_dir()
    overrides = load_score_overrides()
    if etf_code not in overrides:
        overrides[etf_code] = {}
    overrides[etf_code][factor] = new_score
    overrides[etf_code]["_updated_at"] = datetime.now().isoformat()
    with open(SCORE_OVERRIDES_FILE, "w") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)
    logger.info(f"因子干预已保存: {etf_code}.{factor} = {new_score}")


def clear_score_override(etf_code: str, factor: str = None):
    overrides = load_score_overrides()
    if etf_code in overrides:
        if factor:
            overrides[etf_code].pop(factor, None)
        else:
            del overrides[etf_code]
    with open(SCORE_OVERRIDES_FILE, "w") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)


# ────────────────────────────────────────────────────
# 决策干预（Level 3）
# ────────────────────────────────────────────────────

def load_decision_overrides() -> dict:
    _ensure_dir()
    if DECISION_OVERRIDES_FILE.exists():
        with open(DECISION_OVERRIDES_FILE) as f:
            return json.load(f)
    return {}


def save_decision_override(etf_code: str, signal: str, reason: str):
    _ensure_dir()
    overrides = load_decision_overrides()
    overrides[etf_code] = {
        "signal": signal,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
    }
    with open(DECISION_OVERRIDES_FILE, "w") as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)
    logger.info(f"决策干预已保存: {etf_code} → {signal}，原因: {reason}")


def clear_decision_override(etf_code: str):
    overrides = load_decision_overrides()
    if etf_code in overrides:
        del overrides[etf_code]
        with open(DECISION_OVERRIDES_FILE, "w") as f:
            json.dump(overrides, f, ensure_ascii=False, indent=2)
        logger.info(f"决策干预已清除: {etf_code}")
