from __future__ import annotations

import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # БД
    database_url: str = "postgresql+asyncpg://rs_ito:rs_ito@localhost:5432/rs_ito"
    # URL тестовой БД (используется только в integration-тестах)
    test_database_url: str = "postgresql+asyncpg://rs_ito:rs_ito@postgres:5432/rs_ito_test"
    db_pool_size: int = 20

    # Аутентификация
    jwt_secret_key: str = "CHANGE-ME"  # намеренно короткий — вынуждает настроить .env
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl: int = 1800
    jwt_refresh_token_ttl: int = 2_592_000

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-2.5-flash"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # Эмбеддинги
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # Приложение
    app_port: int = 8010
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    # Демо-аккаунт для защиты диплома (Phase 11 фронта)
    demo_account_enabled: bool = False
    demo_account_email: str = "demo@rsito.student"
    demo_account_password: str = "demo-rsito-2026"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if len(v) < 32:
            msg = "JWT_SECRET_KEY must be at least 32 characters"
            raise ValueError(msg)
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        return not self.debug


settings = Settings()
