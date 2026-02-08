"""
Configuration package.

Provides helpers to load and validate YAML configs under ./config/.
"""

from .loader import (
    ConfigError,
    get_configs,
    load_yaml,
    validate_news_config,
    validate_taide_config,
)

__all__ = [
    "ConfigError",
    "get_configs",
    "load_yaml",
    "validate_news_config",
    "validate_taide_config",
]
