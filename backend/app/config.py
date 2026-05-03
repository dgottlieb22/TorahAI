from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://torah:torah@localhost:5432/torah_search"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    batch_size: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
