"""Runtime configuration management for the Trading AI platform."""

from __future__ import annotations

import importlib.util
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Mapping

try:  # Optional dependency used for secrets.yaml parsing
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency may be absent
    yaml = None


def _load_template_config() -> type:
    """Load the template Config class shipped with the repository."""

    template_path = Path(__file__).with_name("config.template.py")
    spec = importlib.util.spec_from_file_location("config_template", template_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise ImportError(f"Unable to load configuration template from {template_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "Config")


_TEMPLATE_CONFIG = _load_template_config()


def _flatten(mapping: Mapping[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested mapping keys into an uppercase dictionary."""

    flat: Dict[str, Any] = {}
    for key, value in mapping.items():
        if not isinstance(key, str):
            continue
        normalized = key.strip()
        if not normalized:
            continue
        combined = f"{prefix}_{normalized}" if prefix else normalized
        combined_key = combined.upper()
        if isinstance(value, Mapping):
            flat.update(_flatten(value, combined))
        else:
            flat[combined_key] = value
            if prefix:
                flat[normalized.upper()] = value
    return flat


def _read_yaml(path: Path) -> Dict[str, Any]:
    """Read a YAML file if PyYAML is installed and the file exists."""

    if yaml is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if isinstance(data, Mapping):
        return _flatten(data)
    return {}


def _load_secrets() -> Dict[str, Any]:
    """Load secrets from the preferred locations."""

    candidates = []
    env_candidate = os.getenv("TRADING_AI_SECRETS_FILE")
    if env_candidate:
        candidates.append(Path(env_candidate))
    repo_root = Path(__file__).resolve().parents[2]
    candidates.extend(
        [
            repo_root / "secrets.yaml",
            repo_root / "secrets.yml",
            repo_root / "config" / "secrets.yaml",
            repo_root / "config" / "secrets.yml",
        ]
    )

    for candidate in candidates:
        if candidate and candidate.exists():
            secrets = _read_yaml(candidate)
            if secrets:
                return secrets
    return {}


_SECRETS = _load_secrets()


def _lookup_env(name: str) -> Any | None:
    """Return the first matching environment variable for the configuration key."""

    normalized = name.upper()
    candidates = (
        normalized,
        name,
        f"TRADING_AI_{normalized}",
        f"TRADING_AI_{name}",
    )
    for key in candidates:
        if key in os.environ:
            return os.environ[key]

    suffix = f"_{normalized}"
    for key, value in os.environ.items():
        if key.endswith(suffix):
            return value
    return None


def _lookup_secret(name: str) -> Any | None:
    """Return a secret override for the given configuration key."""

    normalized = name.upper()
    candidates = (
        normalized,
        f"TRADING_AI_{normalized}",
    )
    for key in candidates:
        if key in _SECRETS:
            return _SECRETS[key]

    suffix = f"_{normalized}"
    for key, value in _SECRETS.items():
        if key.endswith(suffix):
            return value
    return None


def _coerce_type(value: Any, default: Any) -> Any:
    """Convert environment or secret values to match the default type."""

    if value is None:
        return default

    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    if isinstance(default, int) and not isinstance(value, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    if isinstance(default, float):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    if isinstance(default, (list, tuple, set, frozenset)):
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",") if item.strip()]
        elif isinstance(value, (list, tuple, set, frozenset)):
            parts = [str(item).strip() for item in value if str(item).strip()]
        else:
            parts = [str(value).strip()]
        if isinstance(default, tuple):
            return tuple(parts)
        if isinstance(default, set):
            return set(parts)
        if isinstance(default, frozenset):
            return frozenset(parts)
        return parts

    if isinstance(default, timedelta):
        if isinstance(value, timedelta):
            return value
        try:
            minutes = float(value)
        except (TypeError, ValueError):
            return default
        return timedelta(minutes=minutes)

    return value


def _get_config_value(name: str, default: Any) -> Any:
    """Resolve the effective configuration value for ``name``."""

    env_value = _lookup_env(name)
    if env_value not in (None, ""):
        return _coerce_type(env_value, default)

    secret_value = _lookup_secret(name)
    if secret_value not in (None, ""):
        return _coerce_type(secret_value, default)

    return default


class Config(_TEMPLATE_CONFIG):
    """Configuration object that honours environment variables and secrets."""

    # Additional defaults tailored to the Flask web layer
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    SESSION_DURATION_MINUTES = 10
    SEND_FILE_MAX_AGE_DEFAULT = 31536000
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_PING_TIMEOUT = getattr(_TEMPLATE_CONFIG, "ENHANCED_ANALYSIS_TIMEOUT", 60)
    SOCKETIO_PING_INTERVAL = 25
    CORS_ORIGINS = "*"
    CORS_METHODS = ("GET", "POST", "PUT", "DELETE", "OPTIONS")
    CORS_ALLOW_HEADERS = ("Content-Type", "Authorization")
    CORS_SUPPORTS_CREDENTIALS = False

    # Optional API integrations that are referenced throughout the codebase
    NEWSAPI_API_KEY = ""
    MARKETAUX_API_KEY = ""
    POLYGON_API_KEY = ""


def _apply_overrides() -> None:
    """Apply environment and secrets overrides to the Config class."""

    for attr in dir(Config):
        if not attr.isupper():
            continue
        default = getattr(Config, attr)
        overridden = _get_config_value(attr, default)
        setattr(Config, attr, overridden)

    Config.DEBUG = bool(Config.DEBUG)
    Config.DEBUG_MODE = bool(getattr(Config, "DEBUG_MODE", False) or Config.DEBUG)
    Config.ENV = "development" if Config.DEBUG_MODE else "production"

    Config.PORT = int(getattr(Config, "PORT", 5001))
    Config.HOST = getattr(Config, "HOST", "0.0.0.0")
    Config.WEB_PORT = int(getattr(Config, "WEB_PORT", Config.PORT))
    Config.WEB_HOST = getattr(Config, "WEB_HOST", Config.HOST)

    Config.SESSION_DURATION_MINUTES = int(getattr(Config, "SESSION_DURATION_MINUTES", 10))
    Config.PERMANENT_SESSION_LIFETIME = timedelta(minutes=Config.SESSION_DURATION_MINUTES)

    Config.SEND_FILE_MAX_AGE_DEFAULT = int(getattr(Config, "SEND_FILE_MAX_AGE_DEFAULT", 31536000))
    Config.SOCKETIO_PING_TIMEOUT = int(getattr(Config, "SOCKETIO_PING_TIMEOUT", 60))
    Config.SOCKETIO_PING_INTERVAL = int(getattr(Config, "SOCKETIO_PING_INTERVAL", 25))


_apply_overrides()


__all__ = ["Config"]
