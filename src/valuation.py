"""Run the full valuation for one company and print a readable summary.

Pulls the company snapshot from the database, computes WACC, runs the
Bear/Base/Bull DCF, runs comps, and prints everything in one place.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .comps import run_comps
from .data_loader import get_history, get_snapshot
from .dcf import run_all_scenarios
from .wacc import compute_wacc

LINE = "=" * 64
THIN = "-" * 64


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def run(config_path: str | Path, db_path=None) -> dict:
    cfg = load_config(config_path)
    ticker = cfg["ticker"]
    kwargs = {"db_path": db_path} if db_path else {}

    snap = get_snapshot(ticker, **kwargs)
    history = get_history(ticker, **kwargs)
    wacc = compute_wacc(snap, cfg)
    scenarios = run_all_scenarios(snap, cfg)
    comps = run_comps(ticker, db_path=db_path)

    # -------------------- print summary --------------------
    print(LINE)
    print(f" {cfg['company_name']} ({ticker}) — Intrinsic Valuation")
    print(f" Base year FY{cfg['base_year']} | {cfg['projection_years']}-year DCF "
          f"| FCF method: {cfg['fcf_method']}")
    print(LINE)

    print("\nHISTORICAL FINANCIALS ($m)")
    h = history.copy()
    h["rev_growth_%"] = (h["revenue"].pct_change() * 100).round(1)
    h["ebit_margin_%"] = (h["operating_income"] / h["revenue"] * 100).round(1)
    h["fcf_margin_%"] = (h["free_cash_flow"] / h["revenue"] * 100).round(1)
    print(h[["fiscal_year", "revenue", "rev_growth_%",
             "operating_income", "ebit_margin_%",
             "free_cash_flow", "fcf_margin_%"]].to_string(index=False))

    print("\nCOST OF CAPITAL")
    print(wacc.describe())

    print("\nDCF — VALUE PER SHARE BY SCENARIO")
    print(f"  Current reference price: {snap.price:,.2f}\n")
    header = f"  {'Scenario':<8}{'WACC':>7}{'g':>6}{'EV ($m)':>13}{'Equity ($m)':>14}{'Per share':>12}{'Upside':>9}"
    print(header)
    print("  " + THIN[:len(header) - 2])
    for name in ("bear", "base", "bull"):
        r = scenarios[name]
        print(f"  {name.capitalize():<8}{r.wacc:>6.1%}{r.terminal_growth:>6.1%}"
              f"{r.enterprise_value:>13,.0f}{r.equity_value:>14,.0f}"
              f"{r.value_per_share:>12,.2f}{r.upside_pct:>9.1%}")

    base = scenarios["base"]
    print(f"\n  Base-case terminal value = {base.terminal_pct_of_ev:.0%} of EV "
          f"(healthy range ~50-75%).")

    print("\n  Base-case projection ($m):")
    proj = base.projection.copy()
    proj["revenue"] = proj["revenue"].round(0)
    proj["fcf"] = proj["fcf"].round(0)
    proj["discount_factor"] = proj["discount_factor"].round(3)
    proj["pv_fcf"] = proj["pv_fcf"].round(0)
    print(proj[["year", "revenue", "fcf", "discount_factor", "pv_fcf"]]
          .to_string(index=False))

    print("\nCOMPARABLE COMPANY ANALYSIS")
    print("  Peer trading multiples:")
    print(comps.peer_table.to_string())
    print(f"\n  Peer medians: {comps.median_multiples}")
    print("\n  Implied value per share (apply peer median to target):")
    imp = comps.implied.copy()
    imp["implied_value_per_share"] = imp["implied_value_per_share"].round(2)
    print(imp.to_string(index=False))
    print(f"\n  Comps average implied value per share: {comps.implied_mean:,.2f}")

    print("\nVALUATION RANGE (the 'football field')")
    lo = min(scenarios["bear"].value_per_share, comps.implied_mean)
    hi = max(scenarios["bull"].value_per_share, comps.implied_mean)
    print(f"  DCF bear -> bull : {scenarios['bear'].value_per_share:,.2f} "
          f"-> {scenarios['bull'].value_per_share:,.2f}")
    print(f"  DCF base case    : {base.value_per_share:,.2f}")
    print(f"  Comps average    : {comps.implied_mean:,.2f}")
    print(f"  Blended range    : {lo:,.2f} - {hi:,.2f}  "
          f"(vs price {snap.price:,.2f})")

    if cfg.get("notes"):
        print("\nKEY CAVEATS")
        for note in cfg["notes"]:
            print(f"  - {note}")
    print("\n" + LINE)

    return {"snapshot": snap, "wacc": wacc, "scenarios": scenarios, "comps": comps}
