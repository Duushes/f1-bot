"""Configuration management using pydantic-settings."""

import os
from typing import Set

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load .env file in local environment
if os.getenv("ENV") != "prod":
    load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    import sys
    print("=" * 80, file=sys.stderr)
    print("ERROR: Failed to load configuration!", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"Error: {e}", file=sys.stderr)
    print("\nRequired environment variables:", file=sys.stderr)
    print("  - TELEGRAM_BOT_TOKEN", file=sys.stderr)
    print("  - OPENAI_API_KEY", file=sys.stderr)
    print("  - ADMIN_TELEGRAM_IDS", file=sys.stderr)
    print("\nCurrent environment variables:", file=sys.stderr)
    env_vars = ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY", "ADMIN_TELEGRAM_IDS", "ENV"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "TOKEN" in var or "KEY" in var:
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                print(f"  {var}={masked}", file=sys.stderr)
            else:
                print(f"  {var}={value}", file=sys.stderr)
        else:
            print(f"  {var}=<NOT SET>", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    raise
