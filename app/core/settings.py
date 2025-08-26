from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Task Manager API"
    app_version: str = "2.0.0"
    debug: bool = False

    # БД: по умолчанию SQLite для простого локального запуска
    database_url: str = "sqlite:///./app.db"

    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
