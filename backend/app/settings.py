from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/afo",
        alias="DATABASE_URL",
    )
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gmail_client_id: str = Field(default="", alias="GMAIL_CLIENT_ID")
    gmail_client_secret: str = Field(default="", alias="GMAIL_CLIENT_SECRET")
    gmail_redirect_uri: str = Field(
        default="http://localhost:3000/gmail-callback",
        alias="GMAIL_REDIRECT_URI",
    )
    poll_interval_seconds: int = Field(default=60, alias="POLL_INTERVAL_SECONDS")
    agent_poll_interval_seconds: int = Field(default=10, alias="AGENT_POLL_INTERVAL_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()