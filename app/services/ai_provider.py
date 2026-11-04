"""Frontera AIProvider: hoy Ollama local por HTTP, intercambiable mañana."""
from typing import Protocol

import httpx

import logging
import threading
from datetime import datetime, timezone

from app.core.ai_config import AISettings, CloudSettings, get_ai_settings, get_cloud_settings

log = logging.getLogger("nexo.ai")


class AIProviderError(Exception):
    """kind: disabled | unavailable | timeout | invalid"""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


class AIProvider(Protocol):
    model: str

    def chat(self, system: str, user: str, *, json_format: bool = False, max_chars: int) -> str: ...


class DisabledProvider:
    model = ""

    def chat(self, system: str, user: str, *, json_format: bool = False, max_chars: int) -> str:
        raise AIProviderError("disabled")


class OllamaProvider:
    def __init__(self, settings: AISettings, *, base_url: str | None = None, model: str | None = None,
                 timeout: int | None = None, api_key: str = ""):
        self.settings = settings
        self.base_url = base_url or settings.base_url
        self.model = model or settings.model
        self.timeout = timeout or settings.timeout_seconds
        # La clave solo viaja en el header; nunca en logs ni en mensajes de error.
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def chat(self, system: str, user: str, *, json_format: bool = False, max_chars: int) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0.3},
        }
        if json_format:
            payload["format"] = "json"
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
        except httpx.TimeoutException:
            log.warning("IA %s: timeout (modelo=%s)", self.base_url, self.model)
            raise AIProviderError("timeout")
        except httpx.HTTPError as exc:
            log.warning("IA %s: error de conexión %s", self.base_url, type(exc).__name__)
            raise AIProviderError("unavailable")
        if response.status_code != 200:
            # Solo código y host: nunca la clave ni el contenido de la conversación.
            log.warning("IA %s: HTTP %s (modelo=%s)", self.base_url, response.status_code, self.model)
            raise AIProviderError("unavailable")
        try:
            content = response.json()["message"]["content"]
        except (ValueError, KeyError, TypeError):
            raise AIProviderError("invalid")
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("invalid")
        if len(content) > max_chars:
            raise AIProviderError("invalid")
        return content.strip()


class DailyCap:
    """Tope diario global de llamadas a la nube, en memoria (suficiente para una demo)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.day = None
        self.count = 0

    def take(self, limit: int) -> bool:
        today = datetime.now(timezone.utc).date()
        with self.lock:
            if self.day != today:
                self.day, self.count = today, 0
            if self.count >= limit:
                return False
            self.count += 1
            return True

    def reset(self):
        with self.lock:
            self.day, self.count = None, 0


cloud_cap = DailyCap()


class FallbackProvider:
    """Prueba la nube y, si falla o se agota el tope diario, usa el Ollama local si existe."""

    def __init__(self, cloud: AIProvider | None, cloud_limit: int, local: AIProvider | None):
        self.cloud, self.cloud_limit, self.local = cloud, cloud_limit, local
        self.model = ""

    def chat(self, system: str, user: str, *, json_format: bool = False, max_chars: int) -> str:
        last: AIProviderError | None = None
        if self.cloud is not None and cloud_cap.take(self.cloud_limit):
            try:
                text = self.cloud.chat(system, user, json_format=json_format, max_chars=max_chars)
                self.model = self.cloud.model
                return text
            except AIProviderError as exc:
                last = exc
        if self.local is not None:
            text = self.local.chat(system, user, json_format=json_format, max_chars=max_chars)
            self.model = self.local.model
            return text
        raise last or AIProviderError("unavailable")


def get_ai_provider() -> AIProvider:
    settings = get_ai_settings()
    cloud_cfg: CloudSettings = get_cloud_settings()
    local = OllamaProvider(settings) if settings.enabled else None
    if not cloud_cfg.enabled:
        return local or DisabledProvider()
    cloud = OllamaProvider(
        settings,
        base_url=cloud_cfg.base_url,
        model=cloud_cfg.model,
        timeout=cloud_cfg.timeout_seconds,
        api_key=cloud_cfg.api_key,
    )
    return FallbackProvider(cloud, cloud_cfg.daily_limit, local)
