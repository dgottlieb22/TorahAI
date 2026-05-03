from app.db import SessionLocal
from app.search.semantic import semantic_search
from app.search.keyword import keyword_search


def hybrid_search(query: str, limit: int = 20, session=None) -> list[dict]:
    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        sem_results = semantic_search(query, limit=limit, session=session)
        kw_results = keyword_search(query, limit=limit, session=session)

        sem_max = max((r["score"] for r in sem_results), default=0) or 1
        kw_max = max((r["score"] for r in kw_results), default=0) or 1

        merged: dict[str, dict] = {}
        for r in sem_results:
            merged[r["ref"]] = {
                "ref": r["ref"], "hebrew": r["hebrew"], "english": r["english"],
                "sem_score": r["score"] / sem_max, "kw_score": 0,
            }
        for r in kw_results:
            if r["ref"] in merged:
                merged[r["ref"]]["kw_score"] = r["score"] / kw_max
            else:
                merged[r["ref"]] = {
                    "ref": r["ref"], "hebrew": r["hebrew"], "english": r["english"],
                    "sem_score": 0, "kw_score": r["score"] / kw_max,
                }

        results = []
        for m in merged.values():
            has_sem = m["sem_score"] > 0
            has_kw = m["kw_score"] > 0
            if has_sem and has_kw:
                explanation = "Matched by semantic similarity and keyword search"
            elif has_sem:
                explanation = "Matched by semantic similarity"
            else:
                explanation = "Matched by keyword search"
            results.append({
                "ref": m["ref"], "hebrew": m["hebrew"], "english": m["english"],
                "score": 0.6 * m["sem_score"] + 0.4 * m["kw_score"],
                "explanation": explanation,
            })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]
    finally:
        if own_session:
            session.close()
