# Torah Source Search Engine

Hybrid semantic + keyword search over Torah texts powered by PostgreSQL (pgvector), FastAPI, and OpenAI embeddings.

## Prerequisites

- Docker
- Python 3.12+
- OpenAI API key (optional — works without it using placeholder embeddings)

## Setup

1. **Start database:**
   ```bash
   docker-compose up -d
   ```

2. **Create virtual environment:**
   ```bash
   python3.12 -m venv .venv && source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   cd backend && pip install -r requirements.txt
   ```

4. **Optional — configure OpenAI:**
   ```bash
   # Create backend/.env
   OPENAI_API_KEY=your-key
   ```

5. **Ingest data:**
   ```bash
   cd backend && python -m scripts.ingest /path/to/sefaria/json/dir
   ```

6. **Run embedding worker:**
   ```bash
   cd backend && python -m scripts.run_worker
   ```

7. **Start API:**
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

8. **Search:**
   ```bash
   curl 'http://localhost:8000/search?q=creation+of+world'
   ```

## API

### `GET /search`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q`       | str  | required | Search query |
| `limit`   | int  | 20 | Max results (≤ 100) |

Returns a list of `SearchResult` objects:

```json
[
  {
    "ref": "Genesis 1:1",
    "hebrew": "...",
    "english": "...",
    "score": 0.95,
    "explanation": "Matched by semantic similarity and keyword search"
  }
]
```

### `GET /health`

Returns `{"status": "ok"}`.

## Architecture

| Module | Description |
|--------|-------------|
| `app/main.py` | FastAPI application and route definitions |
| `app/db.py` | SQLAlchemy engine, session factory, and `init_db()` |
| `app/models.py` | `SourceChunk` and `SourceEmbedding` ORM models |
| `app/schemas.py` | Pydantic response models |
| `app/config.py` | Settings via pydantic-settings |
| `app/search/semantic.py` | Semantic search using pgvector cosine distance |
| `app/search/keyword.py` | Full-text keyword search using PostgreSQL `tsvector` |
| `app/search/hybrid.py` | Combines semantic (0.6) and keyword (0.4) scores |
| `scripts/ingest.py` | Ingests Sefaria JSON data into the database |
| `scripts/run_worker.py` | Generates embeddings for ingested texts |
