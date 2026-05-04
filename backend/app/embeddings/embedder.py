from app.config import settings

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(settings.embedding_model)
    return _local_model


def embed(text: str) -> list[float]:
    if settings.use_openai and settings.openai_api_key:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(input=text, model=settings.embedding_model)
        return response.data[0].embedding

    # Local model — multilingual-e5 expects "query: " or "passage: " prefix
    model = _get_local_model()
    vec = model.encode(f"passage: {text}", normalize_embeddings=True)
    return vec.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a search query (uses 'query: ' prefix for e5 models)."""
    if settings.use_openai and settings.openai_api_key:
        return embed(query)

    model = _get_local_model()
    vec = model.encode(f"query: {query}", normalize_embeddings=True)
    return vec.tolist()
