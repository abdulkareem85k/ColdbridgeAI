from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_DB_FILE = BASE_DIR / "coldbridge.db"

class Settings(BaseSettings):
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"
    JWT_SECRET: str = "coldbridge_super_secret_jwt_key_development_only_change_in_production_32chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    FRONTEND_ORIGIN: str = "http://127.0.0.1:5500"
    GOOGLE_MAPS_SERVER_KEY: str = "dummy_server_key"
    ROUTE_CACHE_MINUTES: int = 60
    MAX_ROUTE_CALLS_PER_REQUEST: int = 8
    MAX_ROUTE_CALLS_PER_DAY: int = 100
    LOCATION_FRESHNESS_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
# If DATABASE_URL is a relative sqlite path like sqlite:///./coldbridge.db, convert to absolute path
if settings.DATABASE_URL.startswith("sqlite:///."):
    rel_path = settings.DATABASE_URL.replace("sqlite:///.", "").lstrip("/\\")
    abs_path = (BASE_DIR / rel_path).resolve()
    settings.DATABASE_URL = f"sqlite:///{abs_path.as_posix()}"
