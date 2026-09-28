from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "IT Service Management API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development | production
    DEBUG: bool = False

    DATABASE_URL: str


settings = Settings()
