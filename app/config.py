import logging
from enum import Enum
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class EnvironmentTypes(Enum):
    development = "development"
    testing = "testing"
    production = "production"


class BotSettings(BaseSettings):
    # Environment and debugging
    environment: EnvironmentTypes = EnvironmentTypes.production
    debug: bool = False
    base_dir: Path = Path(__file__).resolve().parent

    # Bot-specific settings
    bot_token: str = ""
    api_url: str = "https://localhost:8000"
    app_url: str = "https://localhost:3000"
    internal_token: str = ""

    mongo_host: str = "localhost"
    mongo_port: int | None = None
    mongo_admin: str = "admin"
    mongo_password: str = ""
    mongo_remote: bool = False

    # Bot behavior settings
    rewind_limit: int = 5
    max_user_media_files: int = 10

    @property
    def mongo_url(self) -> str:
        """Construct the MongoDB connection URL."""
        admin = quote_plus(self.mongo_admin)
        password = quote_plus(self.mongo_password)
        if self.mongo_remote:
            return f"mongodb+srv://{admin}:{password}@{self.mongo_host}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
        return f"mongodb://{admin}:{password}@{self.mongo_host}:{self.mongo_port}"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = BotSettings()
