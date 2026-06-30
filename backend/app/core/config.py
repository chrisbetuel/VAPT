from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    APP_NAME: str = "VAPT Platform"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "UTC"
    PROJECT_NAME: str = "VAPT"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "vapt_user"
    POSTGRES_PASSWORD: str = "vapt_strong_password_2024"
    POSTGRES_DB: str = "vapt"
    DATABASE_URL: Optional[str] = None
    DATABASE_SYNC_URL: Optional[str] = None

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def db_sync_url(self) -> str:
        if self.DATABASE_SYNC_URL:
            return self.DATABASE_SYNC_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        pw = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{pw}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    REDIS_CACHE_TTL: int = 3600
    REDIS_SESSION_TTL: int = 86400

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 7200
    CELERY_TASK_TIME_LIMIT: int = 7800

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # S3 / MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "vapt_minio"
    S3_SECRET_KEY: str = "vapt_minio_secret_2024"
    S3_BUCKET_REPORTS: str = "vapt-reports"
    S3_BUCKET_SCREENSHOTS: str = "vapt-screenshots"
    S3_BUCKET_SCAN_RESULTS: str = "vapt-scan-results"
    S3_REGION: str = "us-east-1"

    # Elasticsearch
    ELASTICSEARCH_ENABLED: bool = True
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_PREFIX: str = "vapt-"

    # Internal
    INTERNAL_API_URL: str = "http://localhost:8000/api/v1/internal/ws-emit"

    # Scanners
    SCANNER_NUCLEI_ENABLED: bool = True
    SCANNER_NUCLEI_CONCURRENCY: int = 10
    SCANNER_ZAP_ENABLED: bool = True
    SCANNER_ZAP_API_KEY: str = "change-me-zap-api-key"
    SCANNER_ZAP_HOST: str = "zap"
    SCANNER_ZAP_PORT: int = 8090
    SCANNER_NMAP_ENABLED: bool = True
    SCANNER_SUBFINDER_ENABLED: bool = True
    SCANNER_FFUF_ENABLED: bool = True
    SCANNER_CUSTOM_ENABLED: bool = True
    SCANNER_MAX_CONCURRENT_SCANS: int = 5
    SCANNER_MAX_RETRIES: int = 3

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # Reports
    REPORTS_DIR: str = "/app/reports"

    # First superuser
    FIRST_SUPERUSER_EMAIL: str = "admin@vapt-platform.com"
    FIRST_SUPERUSER_PASSWORD: str = "Admin123!@#"


settings = Settings()
