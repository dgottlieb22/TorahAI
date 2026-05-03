from sqlalchemy import text as sql_text

from app.db import SessionLocal


def keyword_search(query: str, limit: int = 20, session=None) -> list[dict]:
    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        rows = session.execute(
            sql_text("""
                SELECT c.ref, c.text_he, c.text_en,
                       ts_rank(to_tsvector('simple', coalesce(c.text_he,'') || ' ' || coalesce(c.text_en,'')),
                               plainto_tsquery('simple', :query)) AS rank
                FROM source_chunks c
                WHERE to_tsvector('simple', coalesce(c.text_he,'') || ' ' || coalesce(c.text_en,''))
                      @@ plainto_tsquery('simple', :query)
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"query": query, "limit": limit},
        ).fetchall()
        return [
            {"ref": r.ref, "hebrew": r.text_he, "english": r.text_en, "score": float(r.rank), "source": "keyword"}
            for r in rows
        ]
    finally:
        if own_session:
            session.close()
