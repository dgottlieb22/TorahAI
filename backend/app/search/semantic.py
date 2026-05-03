from sqlalchemy import text as sql_text

from app.db import SessionLocal
from app.embeddings.embedder import embed


def semantic_search(query: str, limit: int = 20, session=None) -> list[dict]:
    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        embedding_vector = embed(query)
        rows = session.execute(
            sql_text("""
                SELECT c.ref, c.text_he, c.text_en,
                       1 - (e.embedding <=> :query_embedding) AS similarity
                FROM source_embeddings e
                JOIN source_chunks c ON c.id = e.chunk_id
                ORDER BY e.embedding <=> :query_embedding
                LIMIT :limit
            """),
            {"query_embedding": str(embedding_vector), "limit": limit},
        ).fetchall()
        return [
            {"ref": r.ref, "hebrew": r.text_he, "english": r.text_en, "score": float(r.similarity), "source": "semantic"}
            for r in rows
        ]
    finally:
        if own_session:
            session.close()
