-- ============================================================
-- analysis_queries.sql — analytical layer over the valuation DB
-- ============================================================
-- A self-contained set of read-only queries that turn the raw rows
-- into the metrics an analyst actually reasons about: growth, margins,
-- cash conversion, KPI trends and peer multiples.
--
-- Run any block interactively:
--     sqlite3 data/valuation.db < sql/analysis_queries.sql
-- ============================================================

-- ------------------------------------------------------------
-- 1. Revenue growth & margin progression (window functions)
--    YoY growth via LAG(); margins as ratios of revenue.
-- ------------------------------------------------------------
SELECT
    f.fiscal_year,
    f.revenue,
    ROUND(100.0 * (f.revenue / LAG(f.revenue) OVER (ORDER BY f.fiscal_year) - 1), 1)
        AS revenue_growth_pct,
    ROUND(100.0 * f.gross_profit     / f.revenue, 1) AS gross_margin_pct,
    ROUND(100.0 * f.operating_income / f.revenue, 1) AS ebit_margin_pct,
    ROUND(100.0 * f.net_income       / f.revenue, 1) AS net_margin_pct,
    ROUND(100.0 * f.free_cash_flow   / f.revenue, 1) AS fcf_margin_pct
FROM financials f
WHERE f.ticker = 'NFLX'
ORDER BY f.fiscal_year;

-- ------------------------------------------------------------
-- 2. Revenue CAGR over the available history (single figure)
--    CAGR = (last / first)^(1/years) - 1
-- ------------------------------------------------------------
WITH bounds AS (
    SELECT
        MIN(fiscal_year) AS first_yr,
        MAX(fiscal_year) AS last_yr
    FROM financials WHERE ticker = 'NFLX'
)
SELECT
    b.first_yr, b.last_yr,
    ROUND(100.0 * (POWER(
        (SELECT revenue FROM financials WHERE ticker='NFLX' AND fiscal_year=b.last_yr) * 1.0 /
        (SELECT revenue FROM financials WHERE ticker='NFLX' AND fiscal_year=b.first_yr),
        1.0 / (b.last_yr - b.first_yr)
    ) - 1), 1) AS revenue_cagr_pct
FROM bounds b;

-- ------------------------------------------------------------
-- 3. Cash conversion: free cash flow vs net income
--    Quality-of-earnings check — FCF/NI above ~1.0 is healthy.
-- ------------------------------------------------------------
SELECT
    fiscal_year,
    net_income,
    free_cash_flow,
    ROUND(free_cash_flow / NULLIF(net_income, 0), 2) AS fcf_to_net_income
FROM financials
WHERE ticker = 'NFLX'
ORDER BY fiscal_year;

-- ------------------------------------------------------------
-- 4. Operating KPI trend — paid memberships & implied ARPU
--    Pivots the tall metrics table; ARPU = revenue / avg members.
-- ------------------------------------------------------------
SELECT
    m.fiscal_year,
    MAX(CASE WHEN m.metric = 'paid_memberships' THEN m.value END) AS paid_members_m,
    f.revenue,
    ROUND(f.revenue / NULLIF(
        MAX(CASE WHEN m.metric = 'paid_memberships' THEN m.value END), 0), 1)
        AS revenue_per_member_usd
FROM operating_metrics m
JOIN financials f
  ON f.ticker = m.ticker AND f.fiscal_year = m.fiscal_year
WHERE m.ticker = 'NFLX'
GROUP BY m.fiscal_year, f.revenue
ORDER BY m.fiscal_year;

-- ------------------------------------------------------------
-- 5. Peer comparable multiples (the heart of the comps analysis)
--    EV = market cap + net debt; multiples computed per peer, then
--    you take the median in the comps engine. P/E excluded where
--    net income <= 0 (e.g. WBD) because the multiple is meaningless.
-- ------------------------------------------------------------
WITH latest AS (
    SELECT
        c.ticker, c.name,
        f.revenue, f.operating_income,
        (f.operating_income + f.d_and_a) AS ebitda,
        f.net_income,
        bs.cash, bs.total_debt, bs.shares_outstanding,
        md.price,
        (md.price * bs.shares_outstanding)                          AS market_cap,
        (md.price * bs.shares_outstanding + bs.total_debt - bs.cash) AS enterprise_value
    FROM companies c
    JOIN financials    f  ON f.ticker  = c.ticker AND f.fiscal_year = 2025
    JOIN balance_sheet bs ON bs.ticker = c.ticker AND bs.fiscal_year = 2025
    JOIN market_data   md ON md.ticker = c.ticker
)
SELECT
    ticker, name,
    ROUND(market_cap, 0)                                   AS market_cap_m,
    ROUND(enterprise_value, 0)                             AS ev_m,
    ROUND(enterprise_value / NULLIF(revenue, 0), 1)        AS ev_sales,
    ROUND(enterprise_value / NULLIF(ebitda, 0), 1)         AS ev_ebitda,
    ROUND(enterprise_value / NULLIF(operating_income, 0), 1) AS ev_ebit,
    CASE WHEN net_income > 0
         THEN ROUND(market_cap / net_income, 1) END        AS pe
FROM latest
ORDER BY ev_sales DESC;
