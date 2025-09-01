from enum import Enum
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentTypes(Enum):
    development = "development"
    testing = "testing"
    production = "production"


class BotSettings(BaseSettings):
    # Environment and debugging
    ENVIRONMENT: EnvironmentTypes
    DEBUG: bool = False
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Bot-specific settings
    BOT_TOKEN: str
    API_URL: str
    APP_URL: str
    INTERNAL_TOKEN: str

    # MongoDB settings (bot sessions only)
    MONGO_HOST: str
    MONGO_PORT: int | None = None
    MONGO_ADMIN: str
    MONGO_PASSWORD: str
    MONGO_REMOTE: bool = False

    # Bot behavior settings
    REWIND_LIMIT: int = 5
    MAX_USER_MEDIA_FILES: int = 10

    @property
    def mongo_url(self):
        admin = quote_plus(self.MONGO_ADMIN)
        password = quote_plus(self.MONGO_PASSWORD)
        if self.MONGO_REMOTE:
            return f"mongodb+srv://{admin}:{password}@{self.MONGO_HOST}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
        return f"mongodb://{admin}:{password}@{self.MONGO_HOST}:{self.MONGO_PORT}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = BotSettings()
