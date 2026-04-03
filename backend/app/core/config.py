from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Evaluaciones Docentes API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "info"
    debug: bool = False
    secret_key: str = "change-this-in-production"
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str = (
        "postgresql+asyncpg://eval_user:eval_pass_dev@localhost:5432/evaluaciones_docentes"
    )
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "minio_pass_dev"
    minio_bucket: str = "evaluaciones"
    minio_secure: bool = False

    # Gemini
    gemini_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
