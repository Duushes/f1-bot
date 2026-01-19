"""Configuration management using pydantic-settings."""

import os
from typing import Set

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# Load .env file in local environment
if os.getenv("ENV") != "prod":
    load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Telegram
    telegram_bot_token: str
    admin_telegram_ids: str  # comma-separated

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # Environment
    env: str = "local"
    log_level: str = "INFO"

    # Database
    db_url: str = "sqlite:///data/app.db"

    # Timezone
    timezone: str = "Asia/Makassar"

    # Language
    lang_default: str = "ru"

    # Optional
    news_sources: str = ""
    f1_calendar_source: str = ""

    @property
    def admin_ids(self) -> Set[int]:
        """Parse admin Telegram IDs from comma-separated string."""
        if not self.admin_telegram_ids:
            return set()
        return {int(uid.strip()) for uid in self.admin_telegram_ids.split(",") if uid.strip()}

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
