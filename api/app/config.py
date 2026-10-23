"""Runtime settings.

Environment variables override the values in `.env`. See `.env.example` at the
repo root for every switch, including the mock provider and Postgres URL.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/docsense.db"
    llm_provider: str = "auto"
    embedding_provider: str = "local"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: str = "http://localhost:3000"
    max_upload_bytes: int = 15 * 1024 * 1024
    chunk_size: int = 700
    chunk_overlap: int = 100
    retrieval_k: int = 4

    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", Path(".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
