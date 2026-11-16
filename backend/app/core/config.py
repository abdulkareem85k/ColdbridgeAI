import secrets
from pathlib import Path
from typing import Literal, Set
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_DB_FILE = BASE_DIR / "coldbridge.db"

INSECURE_JWT_SECRETS: Set[str] = {
    "coldbridge_super_secret_jwt_key_development_only_change_in_production_32chars",
    "CHANGE_ME_GENERATE_WITH_PYTHON_SECRETS_48_CHARS_MINIMUM",
    "CHANGE_ME",
    "",
}

class Settings(BaseSettings):
    APP_ENV: Literal["development", "testing", "production"] = "development"
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"
    JWT_SECRET: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    FRONTEND_ORIGIN: str = "http://127.0.0.1:5500"
    
    # OpenStreetMap + Leaflet / OSRM Configuration (Open Source, No Google Billing)
    OSRM_ROUTING_URL: str = "https://router.project-osrm.org"
    OSM_USER_AGENT: str = "ColdBridgeAI-Avishkar/1.0"
    
    # Routing and Freshness parameters
    ROUTE_CACHE_MINUTES: int = 60
    MAX_ROUTE_CALLS_PER_REQUEST: int = 8
    MAX_ROUTE_CALLS_PER_DAY: int = 200
    LOCATION_FRESHNESS_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_security_and_paths(self) -> "Settings":
        # 1. Cookie SameSite 'none' requires secure flag across all environments
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("FATAL: COOKIE_SAMESITE='none' requires COOKIE_SECURE=True to prevent browser rejection.")

        # 2. Production environment validation
        if self.APP_ENV == "production":
            if (
                not self.JWT_SECRET
                or self.JWT_SECRET in INSECURE_JWT_SECRETS
                or self.JWT_SECRET.startswith("CHANGE_ME")
                or len(self.JWT_SECRET) < 32
            ):
                raise ValueError(
                    "FATAL: In production (APP_ENV=production), JWT_SECRET must be set to a secure, "
                    "unique string of at least 32 characters. Do not use default or placeholder values."
                )
            if not self.COOKIE_SECURE:
                raise ValueError(
                    "FATAL: In production (APP_ENV=production), COOKIE_SECURE must be True (HTTPS required)."
                )
        else:
            # 3. Development / Testing: if missing or placeholder, generate an ephemeral random secret
            if (
                not self.JWT_SECRET
                or self.JWT_SECRET in INSECURE_JWT_SECRETS
                or self.JWT_SECRET.startswith("CHANGE_ME")
            ):
                self.JWT_SECRET = secrets.token_urlsafe(48)
                print("WARNING: JWT_SECRET was missing or placeholder; generated an ephemeral development secret.")

        # 4. Resolve relative sqlite path to absolute path
        if self.DATABASE_URL.startswith("sqlite:///."):
            rel_path = self.DATABASE_URL.replace("sqlite:///.", "").lstrip("/\\")
            abs_path = (BASE_DIR / rel_path).resolve()
            self.DATABASE_URL = f"sqlite:///{abs_path.as_posix()}"

        return self

settings = Settings()
