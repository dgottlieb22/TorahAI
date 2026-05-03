from app.models import SourceChunk
from app.utils.hashing import compute_hash
from app.utils.text import build_embedding_text


def load_chunks(chunks: list[dict], session) -> dict:
    counts = {"inserted": 0, "updated": 0, "skipped": 0}
    for c in chunks:
        emb_text = build_embedding_text(c["ref"], c["category"], c["text_he"], c["text_en"])
        h = compute_hash(emb_text)
        existing = session.query(SourceChunk).filter_by(ref=c["ref"]).first()
        if existing is None:
            session.add(SourceChunk(
                ref=c["ref"], book=c["book"], category=c["category"],
                text_he=c["text_he"], text_en=c["text_en"],
                embedding_text=emb_text, embedding_text_hash=h,
                embedding_status="pending",
            ))
            counts["inserted"] += 1
        elif existing.embedding_text_hash != h:
            existing.text_he = c["text_he"]
            existing.text_en = c["text_en"]
            existing.embedding_text = emb_text
            existing.embedding_text_hash = h
            existing.embedding_status = "pending"
            counts["updated"] += 1
        else:
            counts["skipped"] += 1
    session.commit()
    return counts
