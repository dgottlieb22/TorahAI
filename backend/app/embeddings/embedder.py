import hashlib
import math
import struct

from app.config import settings


def embed(text: str) -> list[float]:
    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(input=text, model=settings.embedding_model)
        return response.data[0].embedding

    # Deterministic placeholder for testing without OpenAI
    dim = settings.embedding_dim
    digest = hashlib.sha256(text.encode()).digest()
    vec = []
    for i in range(dim):
        h = hashlib.sha256(digest + i.to_bytes(4, "little")).digest()
        val = (struct.unpack("<I", h[:4])[0] / 0xFFFFFFFF) * 2 - 1  # [-1, 1]
        vec.append(val)
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec]
