# Netflix (NFLX) — valuation walkthrough

A narrative pass over what the framework produces and how to read it. Reproduce any number with `python run_valuation.py`, or explore the data directly with the queries in [`../sql/analysis_queries.sql`](../sql/analysis_queries.sql).

## 1. The business, in numbers

Pulling Netflix's history from the database (FY2022–FY2025):

| FY | Revenue ($m) | YoY | EBIT margin | FCF margin |
|----|-------------|-----|-------------|-----------|
| 2022 | 31,616 | — | 17.8% | 5.1% |
| 2023 | 33,723 | +6.7% | 20.6% | 20.5% |
| 2024 | 39,001 | +15.7% | 26.7% | 17.7% |
| 2025 | 45,183 | +15.9% | 29.5% | 21.0% |

Two things stand out. First, **margin expansion**: operating margin has climbed from ~18% to ~30% in three years as the business scaled and the password-sharing crackdown plus the ad tier added high-incremental-margin revenue. Second, the **free-cash-flow inflection**: Netflix spent years cash-negative funding content; FY2023 onward it generates real cash, reaching ~\$9.5bn in FY2025. A valuation has to decide how far that margin and cash-flow trajectory runs.

## 2. Cost of capital

Using CAPM with a ~4.3% risk-free rate, a beta of ~1.2 and a 5.5% equity-risk premium gives a cost of equity near **10.9%**. Netflix carries some debt but is overwhelmingly equity-funded, so the market-value debt weight is ~1% and **WACC lands at ~10.8%** — essentially the cost of equity. (As Netflix matures and de-risks, a case can be made for a lower discount rate; the bull scenario tests ~8.5%.)

## 3. DCF

Projecting five years of revenue and free cash flow, discounting at WACC (mid-year convention), and adding a Gordon-growth terminal value:

| Scenario | WACC | Terminal g | Value / share |
|----------|------|-----------|--------------|
| Bear | 11.5% | 2.5% | ~\$35 |
| **Base** | **10.8%** | **3.0%** | **~\$52** |
| Bull | 8.5% | 3.5% | ~\$115 |

The base case anchors to management's FY2026 guidance (~\$51bn revenue, 31.5% operating-margin target) and tapers growth toward GDP while FCF margin ramps into the high-20s. Terminal value is ~74% of enterprise value — high, but expected for a still-growing company, and within a defensible range.

## 4. Comps

Netflix's peer set (Disney, Comcast, Warner Bros. Discovery, Spotify, Paramount Skydance) trades at a **median of ~2× sales**. Applying the peer medians across EV/Sales, EV/EBITDA, EV/EBIT and P/E gives an average implied value near **\$50/share** — but this understates Netflix, because Netflix itself trades at ~10× sales and ~42× earnings. The comps mainly make the point that **Netflix commands a large premium to legacy media**, which only its superior growth and margins justify.

> P/E is excluded for Warner Bros. Discovery because it is loss-making — a negative or vanishing P/E is meaningless and would distort the median.

## 5. Putting it together

The valuation range — DCF bear-to-bull of **~\$35 to ~\$115**, base ~\$52, comps ~\$50 — sits mostly **below** the ~\$110 reference price, with only the bull case bracketing it.

The honest read: this is not a model that conveniently reproduces the market price, and it shouldn't be. Netflix is a high-quality, cash-generative business, but at the reference price the market is already paying for the bull case — sustained high-teens growth, FCF margins into the low-30s, *and* a lower cost of capital. That leaves **limited margin of safety**. A disciplined investor would want either a lower entry price or conviction that reality beats the base case.

## What would change the answer

- **The Warner Bros. acquisition** (announced Dec-2025, all-cash, ~\$72bn equity value) is deliberately *not* modelled here. It would materially change debt, the share count and the growth/margin profile, and deserves its own scenario.
- **Discount rate** is the single biggest lever in a terminal-value-heavy DCF — the gap between the base (~10.8%) and bull (8.5%) WACC explains most of the difference between ~\$52 and ~\$115.
- **Refresh the inputs**: peer multiples here are illustrative placeholders, and the share price is a post-split reference — update both before citing any output.
