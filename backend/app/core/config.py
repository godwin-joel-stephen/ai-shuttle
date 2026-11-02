from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    database_url: str
    app_env: str = "development"
    gemini_api_key: str
    # Tier 1 model per the LLM architecture doc; raise to
    # gemini-3.5-flash-lite if evaluation shows tool use is unreliable.
    agent_model: str = "gemini-3.1-flash-lite"
    # Used for a step when the primary model errors (e.g. Google's 503
    # "high demand"), so an overloaded model doesn't fail the conversation.
    agent_fallback_model: str = "gemini-3.5-flash-lite"

    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()