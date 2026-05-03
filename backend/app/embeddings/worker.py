from datetime import datetime, timezone

from app.config import settings
from app.db import SessionLocal
from app.embeddings.embedder import embed
from app.models import SourceChunk, SourceEmbedding


def process_pending(batch_size: int = None) -> dict:
    if batch_size is None:
        batch_size = settings.batch_size
    db = SessionLocal()
    embedded = failed = 0
    try:
        chunks = db.query(SourceChunk).filter(
            SourceChunk.embedding_status == "pending"
        ).limit(batch_size).all()
        for chunk in chunks:
            try:
                vec = embed(chunk.embedding_text)
                emb = db.query(SourceEmbedding).filter_by(
                    chunk_id=chunk.id, embedding_model=settings.embedding_model
                ).first()
                if emb:
                    emb.embedding = vec
                    emb.embedding_text_hash = chunk.embedding_text_hash
                else:
                    db.add(SourceEmbedding(
                        chunk_id=chunk.id,
                        embedding_model=settings.embedding_model,
                        embedding=vec,
                        embedding_text_hash=chunk.embedding_text_hash,
                    ))
                chunk.embedding_status = "embedded"
                chunk.last_embedded_at = datetime.now(timezone.utc)
                chunk.embedding_error = None
                embedded += 1
            except Exception as e:
                chunk.embedding_status = "failed"
                chunk.embedding_error = str(e)
                failed += 1
            db.commit()
    finally:
        db.close()
    return {"embedded": embedded, "failed": failed}
