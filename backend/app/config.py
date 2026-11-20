from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_model: str = "nvidia/nemotron-3.5-super-vl:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    top_k: int = 3
    max_history_messages: int = 6

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()