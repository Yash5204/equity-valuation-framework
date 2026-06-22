# Roadmap

The project is built in phases so each layer is a self-contained, demonstrable skill. All four phases are complete; the cross-cutting items below are optional future polish.

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

## Phase 3 — Interactive dashboard ✅
- `dashboard/app.py`: a Streamlit app reading the same database and reusing the same engine, with four tabs — Valuation (football field, live projection, EV→equity waterfall, WACC × terminal-growth sensitivity heatmap), Financials (revenue/margins/cash flow trends), Operating KPIs (memberships, margin, ad revenue), and Comparables (peer multiples + implied value)
- Sidebar sliders (scenario, WACC, terminal growth, growth/margin shifts) re-run the DCF live; built with Plotly; deployable free on Streamlit Community Cloud for a live CV link
- **Demonstrates:** data visualisation & communicating analysis interactively — core to Analyst / BA roles

## Phase 4 — Pitch deck + investment memo ✅
- `outputs/NFLX_Investment_Pitch.pptx`: a 12-slide deck — investment summary, company overview, business model, financial trends, valuation approach, scenario football field, comparables, sensitivity, risks/catalysts, recommendation, and a methodology appendix
- `docs/INVESTMENT_MEMO.md`: a tight 1–2 page written memo (thesis, business, valuation, scenarios, risks, conclusion)
- Both built from the same engine-exported figures, so the narrative matches the model exactly
- **Demonstrates:** business communication & storytelling — translating the model into a decision

## Cross-cutting (optional polish)
- Live data ingestion (e.g. pull financials from an API into the database instead of seeding by hand)
- Unit tests for the valuation math (assert the bridge, terminal-value share of EV, etc.)
- A second worked company (e.g. Spotify) to prove the framework is genuinely reusable
