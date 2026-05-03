from fastapi import FastAPI, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import init_db, get_db
from app.search.hybrid import hybrid_search
from app.schemas import SearchResult

app = FastAPI(title="Torah Search")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return FileResponse("app/static/index.html")


@app.get("/search", response_model=list[SearchResult])
def search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    return hybrid_search(q, limit, session=db)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory="app/static"), name="static")
