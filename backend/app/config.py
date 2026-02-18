from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "UPS Pricing Intelligence"
    debug: bool = False
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/ups_pricing.db"
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
