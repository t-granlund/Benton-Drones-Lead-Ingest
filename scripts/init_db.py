from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lead_ingest.db import DEFAULT_DB_PATH, connect, init_db

with connect(DEFAULT_DB_PATH) as conn:
    init_db(conn)

print(f"Initialized database at {DEFAULT_DB_PATH}")
