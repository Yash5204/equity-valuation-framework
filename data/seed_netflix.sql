-- ============================================================
-- Seed data — Netflix (target) + streaming/media peer set
-- ============================================================
-- PROVENANCE
--   * NETFLIX financials (FY2022-FY2025) are ACTUALS, sourced from
--     Netflix's FY2025 shareholder letter / 10-K and corroborating
--     financial data providers (revenue, operating income, net income,
--     operating cash flow and free cash flow). Share count reflects the
--     10-for-1 stock split effected 14-Nov-2025 (~4.22bn shares).
--   * d_and_a for Netflix is an ESTIMATE dominated by content
--     amortisation — see the FCF note in config/netflix.yaml for why the
--     DCF uses an FCF-margin method rather than a textbook D&A add-back.
--   * PEER rows (DIS, CMCSA, WBD, SPOT, PSKY) are ILLUSTRATIVE,
--     rounded placeholders so the comps engine is fully runnable.
--     >>> Refresh these from your data source before citing any output. <<<
-- All monetary values in $ millions; shares in millions.
-- ============================================================

-- ---------- Companies ----------
INSERT INTO companies (ticker, name, sector, currency) VALUES
  ('NFLX',  'Netflix, Inc.',                 'Streaming / Media', 'USD'),
  ('DIS',   'The Walt Disney Company',       'Media / Entertainment', 'USD'),
  ('CMCSA', 'Comcast Corporation',           'Media / Telecom', 'USD'),
  ('WBD',   'Warner Bros. Discovery, Inc.',  'Media / Entertainment', 'USD'),
  ('SPOT',  'Spotify Technology S.A.',       'Audio Streaming', 'USD'),
  ('PSKY',  'Paramount Skydance Corporation','Media / Entertainment', 'USD');

-- ---------- Netflix financials (ACTUALS, FY2022-FY2025) ----------
INSERT INTO financials
  (ticker, fiscal_year, revenue, gross_profit, operating_income, d_and_a, net_income, operating_cash_flow, capex, free_cash_flow) VALUES
  ('NFLX', 2022, 31616, 12447,  5633, 14500,  4492,  2000,  380,  1620),
  ('NFLX', 2023, 33723, 14008,  6954, 14800,  5408,  7270,  350,  6920),
  ('NFLX', 2024, 39001, 17963, 10418, 15500,  8712,  7400,  478,  6922),
  ('NFLX', 2025, 45183, 21908, 13327, 16400, 10981, 10100,  688,  9500);

-- ---------- Netflix balance sheet (most recent: FY2025) ----------
INSERT INTO balance_sheet (ticker, fiscal_year, cash, total_debt, shares_outstanding) VALUES
  ('NFLX', 2025, 9000, 14460, 4220);

-- ---------- Netflix operating KPIs (for the data/BA + dashboard layer) ----------
INSERT INTO operating_metrics (ticker, fiscal_year, metric, value, unit) VALUES
  ('NFLX', 2024, 'paid_memberships', 301.6, 'millions'),
  ('NFLX', 2025, 'paid_memberships', 325.0, 'millions'),
  ('NFLX', 2025, 'ad_revenue',       1500.0, 'usd_millions'),
  ('NFLX', 2025, 'ucan_revenue_q4',  5340.0, 'usd_millions'),
  ('NFLX', 2025, 'operating_margin', 29.5,   'percent'),
  ('NFLX', 2024, 'operating_margin', 26.7,   'percent');

-- ---------- Netflix market snapshot (REFRESH price before use) ----------
INSERT INTO market_data (ticker, as_of_date, price, beta) VALUES
  ('NFLX', '2026-01-20', 110.00, 1.20);

-- ============================================================
-- PEERS — ILLUSTRATIVE placeholders. Refresh before citing.
-- ============================================================
INSERT INTO financials
  (ticker, fiscal_year, revenue, gross_profit, operating_income, d_and_a, net_income, operating_cash_flow, capex, free_cash_flow) VALUES
  ('DIS',   2025, 94000, 31000, 12000,  5000,  6000, 14000,  5000,  9000),
  ('CMCSA', 2025,124000, 86000, 24000, 14000, 16000, 28000, 12000, 16000),
  ('WBD',   2025, 39000, 17000,  3000,  6000, -3000,  6000,  1200,  4800),
  ('SPOT',  2025, 18000,  5400,  1500,   200,  1300,  2400,   100,  2300),
  ('PSKY',  2025, 29000, 10000,  2500,  1500,  1000,  3000,   800,  2200);

INSERT INTO balance_sheet (ticker, fiscal_year, cash, total_debt, shares_outstanding) VALUES
  ('DIS',   2025,  6000, 45000, 1800),
  ('CMCSA', 2025,  6000,100000, 3800),
  ('WBD',   2025,  4000, 38000, 2500),
  ('SPOT',  2025,  8000,  1500,  200),
  ('PSKY',  2025,  3000, 14000,  700);

INSERT INTO market_data (ticker, as_of_date, price, beta) VALUES
  ('DIS',   '2026-01-20', 112.00, 1.20),
  ('CMCSA', '2026-01-20',  38.00, 0.95),
  ('WBD',   '2026-01-20',  18.00, 1.40),
  ('SPOT',  '2026-01-20', 600.00, 1.55),
  ('PSKY',  '2026-01-20',  14.00, 1.30);

-- ---------- Peer group for NFLX ----------
INSERT INTO peer_group (target_ticker, peer_ticker) VALUES
  ('NFLX', 'DIS'),
  ('NFLX', 'CMCSA'),
  ('NFLX', 'WBD'),
  ('NFLX', 'SPOT'),
  ('NFLX', 'PSKY');
