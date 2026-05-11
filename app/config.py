from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    APP_NAME: str = "GitRAG"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_TIMEOUT_SECONDS: int = 10
    GITHUB_MAX_FILE_SIZE_KB: int = 100

    # AnimusAI Embeddings (OpenAI-compatible)
    ANIMUSAI_API_KEY: str
    ANIMUSAI_BASE_URL: str = "https://api.aimlapi.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BATCH_SIZE: int = 100
    EMBEDDING_TIMEOUT_SECONDS: int = 20

    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 1024
    GROQ_TIMEOUT_SECONDS: int = 30
    GROQ_TEMPERATURE: float = 0.1

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_PREFIX: str = "gitrag_"

    # Ingestion limits
    MAX_FILES_PER_REPO: int = 200
    MAX_CHUNKS_PER_FILE: int = 50
    MIN_CHUNK_SIZE_CHARS: int = 50

    # Retry config
    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY_SECONDS: float = 1.0
    RETRY_MAX_DELAY_SECONDS: float = 30.0

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",  # ignore unknown env vars (OPENAI_API_KEY etc.)
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
