from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me"
    api_v1_prefix: str = "/api/v1"

    # Telegram
    telegram_bot_token: str
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "webhook-secret"

    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Admin
    admin_telegram_ids: str = ""  # comma-separated telegram user IDs, e.g. "123456789,987654321"

    # Telegram Stars pricing (1 Star ≈ $0.013 USD)
    stars_monthly_price: int = 190   # ~99 UAH / ~$2.47
    stars_yearly_price: int = 1750   # ~899 UAH / ~$22.75

    # OpenAI
    openai_api_key: str
    openai_text_model: str = "gpt-4o-mini"
    openai_vision_model: str = "gpt-4o"
    openai_whisper_model: str = "whisper-1"
    openai_max_retries: int = 3
    openai_timeout: int = 30

    # AWS S3 / MinIO
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "ai-diet-photos"
    s3_endpoint_url: str = ""  # empty = AWS, set URL for MinIO

    # Subscription limits
    free_daily_text_analyses: int = 10
    free_daily_photo_analyses: int = 3

    # Security
    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Monitoring
    sentry_dsn: str = ""
    log_level: str = "INFO"
    admin_api_key: str = "admin-key"

    # Rate limiting
    rate_limit_messages_per_minute: int = 30
    rate_limit_photos_per_hour: int = 20

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("DATABASE_URL must be a PostgreSQL or SQLite connection string")
        # Railway provides postgresql:// — asyncpg requires postgresql+asyncpg://
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def admin_telegram_ids_set(self) -> frozenset[int]:
        if not self.admin_telegram_ids:
            return frozenset()
        return frozenset(int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip())

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def webhook_path(self) -> str:
        return f"/webhook/{self.telegram_bot_token}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
