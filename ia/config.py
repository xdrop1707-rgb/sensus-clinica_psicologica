from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class IASettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Gemini
    gemini_api_key: SecretStr
    gemini_chat_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768  # deve ser igual ao vector(768) do SQL
    gemini_thinking_budget: int | None = 0  # 0 = sem "thinking" (mais rápido/barato). None = padrão do modelo

    # Supabase (backend usa service_role; NUNCA exponha no front)
    supabase_url: str
    supabase_service_role_key: SecretStr

    # API
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]  # JSON no .env

    # RAG
    rag_top_k: int = 4
    rag_min_similarity: float = 0.55  # calibre com `python -m ia.cli --debug`

    # Geração
    ia_temperature: float = 0.2
    ia_max_output_tokens: int = 1024


@lru_cache
def get_ia_settings() -> IASettings:
    return IASettings()
