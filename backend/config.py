"""
Application configuration using pydantic-settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str = ""

    # Brapi
    brapi_api_key: str = ""

    # WAHA
    waha_api_url: str = "http://waha:3000"
    waha_session_name: str = "default"
    waha_api_key: str = "finbot-secret"

    # ChromaDB
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8080

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
