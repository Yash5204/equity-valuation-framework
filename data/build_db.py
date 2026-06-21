"""Build the SQLite valuation database from the schema and seed files.

Usage:
    python data/build_db.py

Creates data/valuation.db. Safe to re-run — it rebuilds from scratch.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "valuation.db"
SCHEMA = DATA_DIR / "schema.sql"
SEED = DATA_DIR / "seed_netflix.sql"


def build() -> Path:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA.read_text())
        conn.executescript(SEED.read_text())
        conn.commit()

        # quick sanity check
        n_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        n_fin = conn.execute("SELECT COUNT(*) FROM financials").fetchone()[0]
        print(f"Built {DB_PATH.name}: {n_companies} companies, {n_fin} financial rows.")
    finally:
        conn.close()
    return DB_PATH


if __name__ == "__main__":
    build()
