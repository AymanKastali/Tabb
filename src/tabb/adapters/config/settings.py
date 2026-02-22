"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "tabb"
    debug: bool = False
    host: str = "0.0.0.0"  # nosec B104 — required for container networking
    port: int = 8000

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tabb"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_command_timeout: int = 30

    outbox_poll_interval_seconds: float = 1.0

    model_config = {"env_prefix": "TABB_", "env_file": (".env", ".env.dev")}


settings = Settings()
