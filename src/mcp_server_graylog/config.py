"""Configuration from GRAYLOG_* environment variables."""

import base64
import os
from dataclasses import dataclass, field

_TRUE = {"1", "true", "yes", "on"}


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in _TRUE


@dataclass(frozen=True)
class Config:
    url: str = "http://127.0.0.1:9000"
    token: str = field(default="", repr=False)
    timeout: float = 30.0
    verify_tls: bool = True
    read_only: bool = True
    max_chars: int = 100_000

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            url=os.environ.get("GRAYLOG_URL", cls.url).rstrip("/"),
            token=os.environ.get("GRAYLOG_API_TOKEN", ""),
            timeout=float(os.environ.get("GRAYLOG_TIMEOUT", "30")),
            verify_tls=_flag("GRAYLOG_VERIFY_TLS", True),
            read_only=_flag("GRAYLOG_READ_ONLY", True),
            max_chars=int(os.environ.get("GRAYLOG_MAX_CHARS", "100000")),
        )

    @property
    def endpoint(self) -> str:
        return f"{self.url}/api/mcp"

    def auth_header(self) -> str:
        """Graylog expects Basic base64("<api-token>:token")."""
        if not self.token:
            raise RuntimeError("GRAYLOG_API_TOKEN is not set")
        return "Basic " + base64.b64encode(f"{self.token}:token".encode()).decode()
