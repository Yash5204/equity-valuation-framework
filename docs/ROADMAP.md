# Roadmap

The project is built in phases so each layer is a self-contained, demonstrable skill. Phases 1–2 are complete; the rest extend the same single source-of-truth database and config.

## Phase 1 — Analytical core ✅ (this repo)
- Relational SQLite schema for financials, KPIs and peers
- Analytical SQL (window functions, CTEs, ratio & cash-conversion analysis)
- Config-driven **DCF** engine (Bear/Base/Bull, mid-year convention, terminal value)
- **CAPM WACC** and **comparable-company** analysis
- One-command run with a formatted valuation summary
- **Demonstrates:** SQL, Python, financial modelling, structured assumptions

## Phase 2 — Auditable Excel model ✅
- `build_excel_model.py` exports the same DCF to a formula-driven `.xlsx` (nothing hardcoded that should compute)
- Four sheets: **Summary** (outputs + football-field chart), **DCF** (Bear/Base/Bull blocks + two sensitivity tables: WACC × terminal growth and growth × margin), **WACC**, **Comps**
- Blue inputs / black formulas / green cross-sheet links; cell comments citing sources; validated to **zero formula errors**
- Generated from the same `config/netflix.yaml` and database as the engine, so the two reconcile exactly (Bear \$35.23 / Base \$52.35 / Bull \$115.22)
- **Demonstrates:** Excel / investment-banking-standard modelling — still the lingua franca of finance roles

## Phase 3 — Interactive dashboard
- Read the same database into an interactive view: revenue/margin trends, KPI (subscribers, ARPU) charts, peer-multiple comparison, and a live DCF sensitivity slider
- Built in Plotly/Streamlit (fully reproducible from the repo); a Power BI / Tableau version can be built from the same clean tables if a specific role asks for that tool
- **Demonstrates:** data visualisation & communicating analysis interactively — core to Analyst / BA roles

## Phase 4 — Pitch deck + investment memo
- Rebuild the original pitch deck around the new analysis (company overview, business model, financials, valuation bridge, comps, scenarios, risks, recommendation)
- Add a tight 1–2 page written **investment memo** for a non-technical reader
- **Demonstrates:** business communication & storytelling — translating the model into a decision

## Cross-cutting (optional polish)
- Live data ingestion (e.g. pull financials from an API into the database instead of seeding by hand)
- Unit tests for the valuation math (assert the bridge, terminal-value share of EV, etc.)
- A second worked company (e.g. Spotify) to prove the framework is genuinely reusable
