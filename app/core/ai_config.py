"""Configuración de la IA local (Etapa 23). Se lee en cada uso para poder probarla."""
import os
from dataclasses import dataclass
from urllib.parse import urlparse

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except ValueError:
        value = default
    return max(low, min(high, value))


@dataclass(frozen=True)
class AISettings:
    enabled: bool
    provider: str
    base_url: str
    model: str
    timeout_seconds: int
    max_explanation_chars: int
    max_draft_chars: int


def get_ai_settings() -> AISettings:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
    host = urlparse(base_url).hostname
    allow_remote = _bool("AI_ALLOW_REMOTE_HOST", False)
    enabled = _bool("AI_ENABLED", False)
    # Un host no local exige permiso explícito; si no, la IA queda deshabilitada.
    if enabled and host not in LOCAL_HOSTS and not allow_remote:
        enabled = False
    return AISettings(
        enabled=enabled and os.getenv("AI_PROVIDER", "ollama").lower() == "ollama",
        provider="ollama",
        base_url=base_url,
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip() or "qwen2.5:7b",
        timeout_seconds=_int("OLLAMA_TIMEOUT_SECONDS", 30, 2, 120),
        max_explanation_chars=_int("AI_MAX_EXPLANATION_CHARS", 1800, 200, 6000),
        max_draft_chars=_int("AI_MAX_DRAFT_CHARS", 4500, 500, 10000),
    )


@dataclass(frozen=True)
class CloudSettings:
    enabled: bool
    base_url: str
    model: str
    api_key: str
    timeout_seconds: int
    daily_limit: int


def get_cloud_settings() -> CloudSettings:
    """Ollama Cloud (de pago). Solo se activa con bandera explícita y clave; la clave nunca se registra."""
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    model = os.getenv("OLLAMA_CLOUD_MODEL", "").strip()
    return CloudSettings(
        enabled=_bool("AI_CLOUD_ENABLED", False) and bool(api_key) and bool(model),
        base_url=os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com").strip().rstrip("/"),
        model=model,
        api_key=api_key,
        timeout_seconds=_int("OLLAMA_CLOUD_TIMEOUT_SECONDS", 30, 2, 120),
        daily_limit=_int("AI_CLOUD_DAILY_LIMIT", 200, 1, 100000),
    )
