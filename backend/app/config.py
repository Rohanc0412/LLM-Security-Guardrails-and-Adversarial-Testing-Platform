from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    name: str = "LLM Security Guardrails"
    version: str = "0.1.0"
    env: Literal["local", "development", "test", "staging", "production"] = "local"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    api_prefix: str = ""
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_guardrails"
    db_echo: bool = False
    redis_url: str = Field(default="redis://localhost:6379/0")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
