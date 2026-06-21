-- ============================================================
-- Equity Valuation Framework — Relational Schema (SQLite)
-- ============================================================
-- One small, normalised database that powers the whole project:
--   * the DCF engine reads the target company's financials here
--   * the comps engine reads the peer group's financials here
--   * the dashboard reads the same tables, so every layer agrees
--
-- Design notes:
--   * Money is stored in millions of the company's reporting currency.
--   * Peers are modelled as ordinary rows in `companies` so the same
--     tables serve both the target and its comparables.
--   * Operating KPIs (subscribers, ARPU, regional revenue) live in a
--     tall/EAV table so any company can carry its own metrics without
--     schema changes — useful for the data-analyst / BA layer.
-- ============================================================

DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS financials;
DROP TABLE IF EXISTS balance_sheet;
DROP TABLE IF EXISTS operating_metrics;
DROP TABLE IF EXISTS market_data;
DROP TABLE IF EXISTS peer_group;

-- Master list of every company in the database (target + peers).
CREATE TABLE companies (
    ticker      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    sector      TEXT,
    currency    TEXT DEFAULT 'USD'
);

-- Income-statement & cash-flow history, one row per fiscal year.
-- All values in $ millions. EBITDA is derived (operating_income + d_and_a).
CREATE TABLE financials (
    ticker              TEXT NOT NULL,
    fiscal_year         INTEGER NOT NULL,
    revenue             REAL,
    gross_profit        REAL,
    operating_income    REAL,   -- EBIT
    d_and_a             REAL,   -- depreciation, amortisation & content amortisation
    net_income          REAL,
    operating_cash_flow REAL,
    capex               REAL,   -- purchases of PP&E (NOT content spend for streamers)
    free_cash_flow      REAL,   -- as reported by the company (OCF - capex)
    PRIMARY KEY (ticker, fiscal_year),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

-- Balance-sheet items needed to bridge enterprise value to equity value.
CREATE TABLE balance_sheet (
    ticker              TEXT NOT NULL,
    fiscal_year         INTEGER NOT NULL,
    cash                REAL,   -- cash + short-term investments, $m
    total_debt          REAL,   -- short- + long-term debt, $m
    shares_outstanding  REAL,   -- diluted shares, millions
    PRIMARY KEY (ticker, fiscal_year),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

-- Flexible store for non-financial operating KPIs (subs, ARPU, regions...).
CREATE TABLE operating_metrics (
    ticker       TEXT NOT NULL,
    fiscal_year  INTEGER NOT NULL,
    metric       TEXT NOT NULL,   -- e.g. 'paid_memberships', 'arpu', 'ucan_revenue'
    value        REAL,
    unit         TEXT,            -- e.g. 'millions', 'usd_per_month', 'usd_millions'
    PRIMARY KEY (ticker, fiscal_year, metric),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

-- Latest market snapshot used for market cap, WACC weights and upside/downside.
CREATE TABLE market_data (
    ticker      TEXT PRIMARY KEY,
    as_of_date  TEXT,
    price       REAL,   -- share price in reporting currency
    beta        REAL,   -- 5y levered equity beta vs market
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

-- Maps a target company to the peers used in its comparable analysis.
CREATE TABLE peer_group (
    target_ticker TEXT NOT NULL,
    peer_ticker   TEXT NOT NULL,
    PRIMARY KEY (target_ticker, peer_ticker),
    FOREIGN KEY (target_ticker) REFERENCES companies(ticker),
    FOREIGN KEY (peer_ticker)   REFERENCES companies(ticker)
);
