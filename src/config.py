from __future__ import annotations

from typing import Any, Dict
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def _project_root() -> Path:
    # src/config.py -> src -> project root
    return Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    if yaml is None:
        # 沒裝 pyyaml 就回空，避免炸
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_configs() -> Dict[str, Any]:
    """
    Return a unified config dict.
    Currently loads: config/news.yaml -> {"news": {...}}
    """
    root = _project_root()
    news_path = root / "config" / "news.yaml"
    news_cfg = _load_yaml(news_path)

    return {"news": news_cfg}
