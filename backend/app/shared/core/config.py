from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Gestión Académica API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "info"
    debug: bool = False
    secret_key: SecretStr = SecretStr("change-this-in-production")
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis
    redis_url: str = ""

    # MinIO
    minio_endpoint: str
    minio_access_key: str = ""
    minio_secret_key: SecretStr = SecretStr("")
    minio_bucket: str = "evaluaciones"
    minio_secure: bool = False

    # Auth / JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480  # 8 hours

    # Gemini
    gemini_api_key: SecretStr = SecretStr("")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        if self.environment not in ("development", "testing"):
            if self.secret_key.get_secret_value() == "change-this-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed from the default in non-development environments"
                )
        return self

    @property
    def is_development(self) -> bool:
        return self.environment in ("development", "testing")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
