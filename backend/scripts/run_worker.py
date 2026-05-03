import sys
import time

sys.path.insert(0, ".")

from app.db import init_db
from app.embeddings.worker import process_pending

if __name__ == "__main__":
    once = "--once" in sys.argv
    init_db()
    while True:
        result = process_pending()
        total = result["embedded"] + result["failed"]
        print(f"Processed: {result['embedded']} embedded, {result['failed']} failed")
        if once:
            break
        if total == 0:
            print("No pending chunks, sleeping 5s...")
            time.sleep(5)
            break
