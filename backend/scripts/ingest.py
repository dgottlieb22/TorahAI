"""Ingest Sefaria JSON files into the database.

Usage: python -m scripts.ingest <directory>
"""
import sys
from pathlib import Path

from app.db import SessionLocal, init_db
from app.ingestion.parser import parse_sefaria_file
from app.ingestion.chunker import chunk_parsed
from app.ingestion.loader import load_chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    init_db()
    session = SessionLocal()
    totals = {"inserted": 0, "updated": 0, "skipped": 0}

    json_files = sorted(directory.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {directory}")

    for filepath in json_files:
        entries = parse_sefaria_file(str(filepath))
        chunks = chunk_parsed(entries)
        counts = load_chunks(chunks, session)
        print(f"  {filepath.name}: {len(chunks)} chunks -> "
              f"inserted={counts['inserted']} updated={counts['updated']} skipped={counts['skipped']}")
        for k in totals:
            totals[k] += counts[k]

    session.close()
    print(f"\nDone. Totals: inserted={totals['inserted']} updated={totals['updated']} skipped={totals['skipped']}")


if __name__ == "__main__":
    main()
