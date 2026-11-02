from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str
    app_env: str = "development"
    gemini_api_key: str
    # Measured 2026-11-02: gemini-3.1-flash-lite (the doc's Tier 1) took
    # 20-47s per call under Google's load and often returned 503, while
    # gemini-3.5-flash-lite (Tier 2) answered in ~1s. Latency is a hard
    # requirement for Siri, so Tier 2 is the primary.
    agent_model: str = "gemini-3.5-flash-lite"
    # Used for a step when the primary model errors or misses its deadline.
    agent_fallback_model: str = "gemini-3.5-flash"

    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()