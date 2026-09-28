from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "IT Service Management API"
    VERSION: str = "0.3.0"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = False

    DATABASE_URL: str

    # JWT (no default on purpose: the app refuses to start without a real secret)
    SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Used only by `python -m app.scripts.create_admin`
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_FULL_NAME: str = "System Administrator"


settings = Settings()
