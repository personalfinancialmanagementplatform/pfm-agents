from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml


class ConfigError(ValueError):
    """Raised when config files are missing, invalid, or contradictory."""


# 專案根目錄推斷：src/config/loader.py -> src/config -> src -> (repo root)
_REPO_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_TAIDE_PATH = _REPO_ROOT / "config" / "model" / "taide.yaml"
_DEFAULT_NEWS_PATH = _REPO_ROOT / "config" / "model" / "news.yaml"

# 簡單的 in-process cache（避免每次 import/呼叫都讀檔）
_CACHE: Dict[Tuple[str, float], Dict[str, Any]] = {}


def load_yaml(path: str | Path) -> Dict[str, Any]:
    """Load a YAML file into a dict with basic validation."""
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Config file not found: {p}")

    # 依檔案修改時間做 cache key
    mtime = p.stat().st_mtime
    cache_key = (str(p), mtime)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ConfigError(f"YAML root must be a mapping (dict): {p}")

    _CACHE[cache_key] = data
    return data


def _get(d: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Safely get nested keys like 'a.b.c' from dict."""
    cur: Any = d
    for k in key_path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def validate_taide_config(cfg: Dict[str, Any]) -> None:
    """
    Validate taide.yaml structure & key consistency.
    Keep this minimal: only validate what you truly rely on.
    """
    model_name = _get(cfg, "model.name")
    if not model_name:
        raise ConfigError("taide.yaml missing required key: model.name")

    # inference defaults
    max_new_tokens = _get(cfg, "inference.max_new_tokens")
    if max_new_tokens is not None and (not isinstance(max_new_tokens, int) or max_new_tokens <= 0):
        raise ConfigError("taide.yaml inference.max_new_tokens must be a positive integer")

    # task_configs should be a dict if present
    task_cfgs = _get(cfg, "task_configs", {})
    if task_cfgs is not None and not isinstance(task_cfgs, dict):
        raise ConfigError("taide.yaml task_configs must be a mapping (dict)")

    # quantization sanity
    q_enabled = bool(_get(cfg, "quantization.enabled", False))
    bits = _get(cfg, "quantization.bits", None)
    if q_enabled:
        if bits not in (4, 8):
            raise ConfigError("taide.yaml quantization.bits must be 4 or 8 when quantization.enabled=true")


def validate_news_config(cfg: Dict[str, Any]) -> None:
    """
    Validate news.yaml business rules to prevent contradictions.
    """
    tz = _get(cfg, "meta.timezone")
    if not tz:
        raise ConfigError("news.yaml missing required key: meta.timezone (e.g., Asia/Taipei)")

    # Push consistency
    push_enabled = bool(_get(cfg, "push.enabled", True))
    daily_enabled = bool(_get(cfg, "push.daily.enabled", False))
    if daily_enabled and not push_enabled:
        raise ConfigError("news.yaml contradiction: push.daily.enabled=true but push.enabled=false")

    refresh_enabled = bool(_get(cfg, "push.refresh.enabled", True))
    cooldown = _get(cfg, "push.refresh.cooldown_sec", 0)
    if refresh_enabled and (not isinstance(cooldown, int) or cooldown < 0):
        raise ConfigError("news.yaml push.refresh.cooldown_sec must be a non-negative integer")

    # Dedup rules
    window_hours = _get(cfg, "push.dedup.window_hours", 24)
    if not isinstance(window_hours, int) or window_hours <= 0:
        raise ConfigError("news.yaml push.dedup.window_hours must be a positive integer")

    key_strategy = _get(cfg, "push.dedup.key_strategy", "url_hash")
    if key_strategy not in ("url_hash", "title_time_hash"):
        raise ConfigError("news.yaml push.dedup.key_strategy must be 'url_hash' or 'title_time_hash'")

    # Channels limits
    for ch in ("hot", "personalized"):
        enabled = bool(_get(cfg, f"channels.{ch}.enabled", False))
        limit = _get(cfg, f"channels.{ch}.limit", 0)
        if enabled and (not isinstance(limit, int) or limit <= 0):
            raise ConfigError(f"news.yaml contradiction: channels.{ch}.enabled=true but channels.{ch}.limit is not > 0")

    # Sources sanity
    rss_enabled = bool(_get(cfg, "sources.rss.enabled", False))
    feeds = _get(cfg, "sources.rss.feeds", [])
    if rss_enabled:
        if not isinstance(feeds, list) or len(feeds) == 0:
            raise ConfigError("news.yaml sources.rss.enabled=true but sources.rss.feeds is empty")
        for i, feed in enumerate(feeds):
            if not isinstance(feed, dict) or not feed.get("url"):
                raise ConfigError(f"news.yaml sources.rss.feeds[{i}] must have a url")


def get_configs(
    taide_path: str | Path = _DEFAULT_TAIDE_PATH,
    news_path: str | Path = _DEFAULT_NEWS_PATH,
    *,
    validate: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """
    Load and (optionally) validate all configs needed by the system.

    Returns:
        {
          "taide": <dict>,
          "news": <dict>,
        }
    """
    taide_cfg = load_yaml(taide_path)
    news_cfg = load_yaml(news_path)

    if validate:
        validate_taide_config(taide_cfg)
        validate_news_config(news_cfg)

    return {"taide": taide_cfg, "news": news_cfg}
