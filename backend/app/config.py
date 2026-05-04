from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://torah:torah@localhost:5432/torah_search"
    openai_api_key: str = ""
    embedding_model: str = "intfloat/multilingual-e5-base"
    embedding_dim: int = 768
    batch_size: int = 100
    use_openai: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
