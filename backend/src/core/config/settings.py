from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SEDV_",
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Secure Enterprise Data Vault API"
    jwt_secret: str = Field(default="dev-secret-change-me")
    jwt_issuer: str = "secure-enterprise-data-vault"
    jwt_audience: str = "sedv-demo"
    token_ttl_seconds: int = 1800
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "sedv"
    demo_organization_name: str = "Demo Organization"
    demo_organization_slug: str = "demo-org"
    password_min_length: int = 8
    file_storage_root: str = "data/encrypted"
    file_encryption_key_seed: str = "dev-file-encryption-key"
    file_encryption_key_version: str = "v1"
    max_upload_size_bytes: int = 25 * 1024 * 1024
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_upload_mime_types: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "text/plain",
            "text/csv",
            "application/json",
            "image/png",
            "image/jpeg",
            "image/gif",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
        ]
    )

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
