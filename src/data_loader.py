"""Read-only access layer over the SQLite valuation database.

Keeps SQL in one place so the DCF/comps engines work with plain Python
objects and never embed queries themselves.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "valuation.db"


@dataclass
class CompanySnapshot:
    """Everything the valuation needs about one company at the latest year."""
    ticker: str
    name: str
    latest_year: int
    revenue: float
    operating_income: float
    d_and_a: float
    net_income: float
    free_cash_flow: float
    cash: float
    total_debt: float
    shares_outstanding: float
    price: float
    beta: float

    @property
    def ebitda(self) -> float:
        return self.operating_income + self.d_and_a

    @property
    def net_debt(self) -> float:
        return self.total_debt - self.cash

    @property
    def market_cap(self) -> float:
        return self.price * self.shares_outstanding

    @property
    def enterprise_value(self) -> float:
        return self.market_cap + self.net_debt


def _connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_snapshot(ticker: str, db_path: Path | str = DB_PATH) -> CompanySnapshot:
    """Latest-year snapshot for one company, joining the financial tables."""
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT c.ticker, c.name,
                   f.fiscal_year, f.revenue, f.operating_income, f.d_and_a,
                   f.net_income, f.free_cash_flow,
                   bs.cash, bs.total_debt, bs.shares_outstanding,
                   md.price, md.beta
            FROM companies c
            JOIN financials f
              ON f.ticker = c.ticker
             AND f.fiscal_year = (SELECT MAX(fiscal_year)
                                  FROM financials WHERE ticker = c.ticker)
            JOIN balance_sheet bs ON bs.ticker = c.ticker
            JOIN market_data   md ON md.ticker = c.ticker
            WHERE c.ticker = ?
            """,
            (ticker,),
        ).fetchone()

    if row is None:
        raise ValueError(f"No data found for ticker {ticker!r}")

    return CompanySnapshot(
        ticker=row["ticker"], name=row["name"], latest_year=row["fiscal_year"],
        revenue=row["revenue"], operating_income=row["operating_income"],
        d_and_a=row["d_and_a"], net_income=row["net_income"],
        free_cash_flow=row["free_cash_flow"], cash=row["cash"],
        total_debt=row["total_debt"], shares_outstanding=row["shares_outstanding"],
        price=row["price"], beta=row["beta"],
    )


def get_history(ticker: str, db_path: Path | str = DB_PATH) -> pd.DataFrame:
    """Full annual financial history for a company as a tidy DataFrame."""
    with _connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM financials WHERE ticker = ? ORDER BY fiscal_year",
            conn, params=(ticker,),
        )


def get_peer_tickers(target: str, db_path: Path | str = DB_PATH) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT peer_ticker FROM peer_group WHERE target_ticker = ? ORDER BY peer_ticker",
            (target,),
        ).fetchall()
    return [r["peer_ticker"] for r in rows]
