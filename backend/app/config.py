"""Application configuration management using Pydantic Settings.

Supports environment variable loading from system environment and .env files.
Validates required settings and provides sensible defaults for local development.
"""

from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Sentinel SOC backend."""

    # Project Information
    PROJECT_NAME: str = "Sentinel — Security Monitoring & Incident Response Platform"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Environment & Debug
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = Field(default=True, description="Enable FastAPI debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # Server Binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    # Security & Hashing
    SECRET_KEY: str = Field(
        default="sentinel_insecure_development_secret_key_change_in_production",
        description="Key used for cryptographic signing; must be overridden in production",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours standard SOC shift
    ALGORITHM: str = "HS256"

    # Database Configuration (PostgreSQL primary; supports SQLite fallback for local test execution)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/sentinel_soc",
        description="Primary PostgreSQL database connection string",
    )

    # Ingestion Subsystem Configuration
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=10 * 1024 * 1024,  # 10 MB limit
        description="Maximum accepted file upload size in bytes",
    )
    MAX_RECORDS_PER_IMPORT: int = Field(
        default=10000,
        description="Maximum number of telemetry records processed in a single batch",
    )
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".json", ".jsonl", ".log"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
