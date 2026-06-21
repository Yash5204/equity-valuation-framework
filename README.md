# Equity Valuation Framework — DCF + Comps, demonstrated on Netflix (NFLX)

A reusable, end-to-end equity valuation engine. Point it at any public company by editing one config file and seeding its financials; it produces a **DCF valuation** (Bear / Base / Bull), a **comparable-company analysis**, and a blended valuation range — all from a single source-of-truth database.

This repo is built to show the full analyst toolkit in one place rather than a single polished slide:

| Layer | What it does | Skill it demonstrates | Reads well for |
|------|--------------|----------------------|----------------|
| **SQL data layer** (`data/`, `sql/`) | Normalised SQLite database of financials, KPIs and peers; analytical queries (window functions, CTEs, ratio analysis) | Relational data modelling & SQL | Data Analyst / BA |
| **Valuation engine** (`src/`) | Config-driven DCF, CAPM WACC, and comparable-company analysis in clean, documented Python | Financial modelling & Python | Finance / Equity Research / FP&A |
| **Scenario & assumptions** (`config/`) | Bear/Base/Bull, FCF method, cost-of-capital inputs — separated from the actuals | Structured analytical thinking | All analyst roles |
| **Excel model** (`build_excel_model.py` → `outputs/`) | The same DCF as an auditable, formula-driven workbook with scenarios and sensitivity tables | Excel / IB-standard modelling | Finance / IB |
| **Dashboard** (`dashboard/app.py`) | Interactive Streamlit app: financial trends, KPIs, peer multiples and a live DCF sensitivity | Data visualisation | Analyst / BA |
| **Deck + memo** (Phase 4) | The investment story for a non-technical audience | Business communication | Strategy / BA |

> **Why "framework, not one stock"?** The thing that reads strongest on a portfolio is *"I built an analysis tool,"* not *"I analysed one company."* Netflix is the worked example; swapping in another company is a config + data change, not a rewrite.

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build the database (creates data/valuation.db from schema + seed)
python data/build_db.py

# 3. Run the full valuation (uses config/netflix.yaml by default)
python run_valuation.py

# ...or value a different company once you've added its config + data:
python run_valuation.py config/your_company.yaml

# 4. (Optional) Generate the Excel model -> outputs/NFLX_DCF_Model.xlsx
python build_excel_model.py

# 5. (Optional) Launch the interactive dashboard in your browser
streamlit run dashboard/app.py
```

The run prints historical financials, the WACC build, all three DCF scenarios, the comps table, and a blended valuation range. The Excel model is generated from the *same* config and database, so the workbook and the Python engine always agree.

---

## Methodology (summary)

**DCF.** Free cash flow is projected over a 5-year horizon, discounted at WACC using the **mid-year convention**, and capped with a **Gordon-growth terminal value**. Enterprise value is bridged to equity value (less net debt) and divided by diluted shares.

- **FCF method.** For Netflix the engine uses the company's reported **FCF margin**, ramped over time, rather than a textbook `EBIT(1−t) + D&A − capex − ΔNWC` build-up. Reason: for streamers the real investment is *cash content spend* (amortised through the P&L), so adding back ~\$16bn of content amortisation while subtracting only ~\$0.7bn of PP&E capex would massively overstate cash generation. The build-up method is supported in the engine for companies where it's appropriate.
- **WACC (CAPM).** `Cost of equity = risk-free + β × equity-risk-premium`; after-tax cost of debt weighted by the market-value capital structure. For a near-all-equity company like Netflix, WACC sits just below the cost of equity, as expected.
- **Comps.** Peer trading multiples (EV/Sales, EV/EBITDA, EV/EBIT, P/E) are computed per peer; the peer-set **median** is applied to Netflix's metrics to derive an implied value per share. P/E is excluded where a peer is loss-making (e.g. WBD) because the multiple is meaningless.

All **assumptions** live in `config/netflix.yaml`; all **actuals** live in the database with provenance noted in `data/seed_netflix.sql`. The two are deliberately kept apart.

---

## Sample output (Netflix, base year FY2025)

Netflix grew revenue to **\$45.2bn (+16%)** in FY2025 at a **29.5% operating margin**, with free cash flow of **\$9.5bn**. Running the framework:

| Scenario | WACC | Terminal g | Value / share |
|----------|------|-----------|--------------|
| Bear | 11.5% | 2.5% | ~\$35 |
| **Base** | **10.8%** | **3.0%** | **~\$52** |
| Bull | 8.5% | 3.5% | ~\$115 |
| Comps (avg) | — | — | ~\$50 |

**Reading the result.** Against a post-split reference price of ~\$110, the base-case DCF and the comps both land well below market, while only the bull case brackets it. The interpretation isn't "the model is wrong" — it's that **the market is pricing Netflix for exceptional, sustained execution**: high-teens growth, FCF margins into the low-30s, *and* a lower cost of capital as the business de-risks. Netflix also trades at ~10× sales / ~42× earnings versus a peer median nearer 2× sales — a premium the bull case has to justify. The honest conclusion is a high-quality business with a demanding valuation and limited margin of safety at the reference price.

*(Figures depend on assumptions you can edit; the share price in the data is a reference to refresh against a live quote.)*

---

## Excel model

`build_excel_model.py` writes a fully formula-driven workbook to `outputs/NFLX_DCF_Model.xlsx` — the same valuation a finance audience can open, audit cell by cell, and stress-test:

- **Summary** — key outputs, valuation range, and a football-field chart.
- **DCF** — Bear / Base / Bull blocks (revenue → FCF → discounting → terminal value → equity → per share) plus two sensitivity tables (WACC × terminal growth, and revenue growth × FCF margin).
- **WACC** — the CAPM build.
- **Comps** — peer trading multiples and implied value per share.

It follows standard modelling conventions (blue inputs, black formulas, green cross-sheet links), documents every hardcoded input with a cell comment, and is validated to recalculate with **zero formula errors**. Because the generator reads the same `config/netflix.yaml` and database as the Python engine, the two reconcile to the cent (Bear \$35.23 / Base \$52.35 / Bull \$115.22).

---

## Interactive dashboard

`dashboard/app.py` is a Streamlit app that reads the same database and reuses the same engine, so its numbers match the Python tool and the Excel model. Run it with `streamlit run dashboard/app.py`. It has four tabs:

- **Valuation** — the football-field range, a live scenario projection, an enterprise-to-equity waterfall, and a WACC × terminal-growth sensitivity heatmap.
- **Financials** — revenue/operating-income, margin trends, and operating vs free cash flow across FY2022–25.
- **Operating KPIs** — paid memberships, operating margin and ad revenue from the database.
- **Comparables** — peer trading multiples with Netflix highlighted, and implied value per share.

The sidebar sliders (scenario, WACC, terminal growth, growth/margin shifts) re-run the DCF live. **Deploy a live link for free:** push this repo to GitHub, then at [share.streamlit.io](https://share.streamlit.io) connect the repo and set the main file to `dashboard/app.py` — you'll get a public URL you can put on your CV.

---

## Repository structure

```
equity-valuation-framework/
├── README.md
├── requirements.txt
├── run_valuation.py            # entry point
├── build_excel_model.py        # generates the Excel model from the same config + DB
├── dashboard/
│   └── app.py                  # interactive Streamlit dashboard (same engine + DB)
├── config/
│   └── netflix.yaml            # assumptions + Bear/Base/Bull scenarios (edit me)
├── data/
│   ├── schema.sql              # relational schema (DDL)
│   ├── seed_netflix.sql        # Netflix actuals + illustrative peers (provenance noted)
│   └── build_db.py             # builds data/valuation.db
├── sql/
│   └── analysis_queries.sql    # growth, margins, cash conversion, peer multiples
├── src/
│   ├── data_loader.py          # read-only DB access -> clean Python objects
│   ├── wacc.py                 # CAPM cost of capital
│   ├── dcf.py                  # DCF engine (margin / build-up, scenarios)
│   ├── comps.py                # comparable company analysis
│   └── valuation.py            # orchestrator + formatted summary
├── notebooks/
│   └── 01_netflix_walkthrough.md
├── outputs/
│   └── NFLX_DCF_Model.xlsx     # generated Excel model (reconciles with the engine)
└── docs/
    └── ROADMAP.md              # what each build phase adds
```

---

## Roadmap

**Phases 1–3 are built**: the analytical core (Python + SQL), the auditable **Excel model**, and the interactive **Streamlit dashboard**. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's left: a rebuilt **pitch deck + investment memo** for the non-technical audience.

---

## Disclaimer

For educational and portfolio purposes only. Not investment advice. Netflix financials are sourced from public filings; **peer multiples are illustrative placeholders** and the reference share price should be refreshed before any output is cited. Do your own due diligence.
