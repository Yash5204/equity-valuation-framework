"""Entry point for the equity valuation framework.

Usage:
    python run_valuation.py                      # uses config/netflix.yaml
    python run_valuation.py config/spotify.yaml  # any other company config

Builds the SQLite database on first run, then prints the full valuation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from data.build_db import build, DB_PATH  # noqa: E402
from src.valuation import run             # noqa: E402


def main() -> None:
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/netflix.yaml"

    if not DB_PATH.exists():
        build()

    run(ROOT / config_path)


if __name__ == "__main__":
    main()
