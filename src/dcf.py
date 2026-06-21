"""Discounted Cash Flow engine.

Projects free cash flow over the forecast horizon, discounts it at WACC
(mid-year convention), adds a Gordon-growth terminal value, then bridges
enterprise value to an intrinsic value per share. Runs Bear / Base / Bull
scenarios from the config.

Two FCF methods are supported (see config):
  * "margin"  : FCF = revenue * fcf_margin   (used for streamers where
                content accounting makes a textbook build-up misleading)
  * "buildup" : FCF = EBIT*(1-tax) + D&A - capex - dNWC
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .data_loader import CompanySnapshot
from .wacc import compute_wacc


@dataclass
class DcfResult:
    scenario: str
    wacc: float
    terminal_growth: float
    projection: pd.DataFrame          # year-by-year revenue, fcf, discount factor, PV
    pv_explicit: float                # sum of discounted explicit-period FCF
    terminal_value: float             # undiscounted TV
    pv_terminal: float                # discounted TV
    enterprise_value: float
    equity_value: float
    value_per_share: float
    current_price: float
    notes: list[str] = field(default_factory=list)

    @property
    def upside_pct(self) -> float:
        return self.value_per_share / self.current_price - 1

    @property
    def terminal_pct_of_ev(self) -> float:
        return self.pv_terminal / self.enterprise_value


def _project_fcf(snap: CompanySnapshot, cfg: dict, scn: dict) -> pd.DataFrame:
    """Build the year-by-year revenue and unlevered FCF projection."""
    base_year = cfg["base_year"]
    growth = scn["revenue_growth"]
    n = len(growth)

    rows = []
    revenue = snap.revenue
    for i in range(n):
        year = base_year + i + 1
        revenue = revenue * (1 + growth[i])

        if cfg["fcf_method"] == "margin":
            fcf = revenue * scn["fcf_margin"][i]
        elif cfg["fcf_method"] == "buildup":
            # EBIT -> NOPAT -> + D&A - capex - dNWC, all as % of revenue
            bu = scn["buildup"]
            ebit = revenue * bu["ebit_margin"][i]
            nopat = ebit * (1 - cfg["tax_rate"])
            da = revenue * bu["da_pct"][i]
            capex = revenue * bu["capex_pct"][i]
            dnwc = (revenue - rows[-1]["revenue"] if rows else 0.0) * bu["nwc_pct_of_growth"][i]
            fcf = nopat + da - capex - dnwc
        else:
            raise ValueError(f"Unknown fcf_method: {cfg['fcf_method']!r}")

        rows.append({"year": year, "revenue": revenue, "fcf": fcf})

    return pd.DataFrame(rows)


def run_dcf(snap: CompanySnapshot, cfg: dict, scenario: str) -> DcfResult:
    scn = cfg["scenarios"][scenario]

    # WACC and terminal growth, with optional per-scenario overrides.
    base_wacc = compute_wacc(snap, cfg).wacc
    wacc = scn.get("wacc_override") or base_wacc
    g_term = scn.get("terminal_growth_override") or cfg["terminal_growth_rate"]
    if g_term >= wacc:
        raise ValueError(
            f"Terminal growth ({g_term:.1%}) must be below WACC ({wacc:.1%})."
        )

    proj = _project_fcf(snap, cfg, scn)
    n = len(proj)

    # Mid-year convention: a cash flow in year t is discounted at t-0.5.
    offset = 0.5 if cfg.get("mid_year_convention", True) else 0.0
    periods = [(i + 1) - offset for i in range(n)]
    proj["period"] = periods
    proj["discount_factor"] = [1 / (1 + wacc) ** p for p in periods]
    proj["pv_fcf"] = proj["fcf"] * proj["discount_factor"]

    pv_explicit = proj["pv_fcf"].sum()

    # Gordon-growth terminal value on the final-year FCF.
    final_fcf = proj["fcf"].iloc[-1]
    terminal_value = final_fcf * (1 + g_term) / (wacc - g_term)
    pv_terminal = terminal_value * proj["discount_factor"].iloc[-1]

    enterprise_value = pv_explicit + pv_terminal
    equity_value = enterprise_value - snap.net_debt
    value_per_share = equity_value / snap.shares_outstanding

    return DcfResult(
        scenario=scenario,
        wacc=wacc,
        terminal_growth=g_term,
        projection=proj,
        pv_explicit=pv_explicit,
        terminal_value=terminal_value,
        pv_terminal=pv_terminal,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        value_per_share=value_per_share,
        current_price=snap.price,
        notes=cfg.get("notes", []),
    )


def run_all_scenarios(snap: CompanySnapshot, cfg: dict) -> dict[str, DcfResult]:
    return {name: run_dcf(snap, cfg, name) for name in cfg["scenarios"]}
