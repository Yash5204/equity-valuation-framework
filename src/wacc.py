"""Weighted Average Cost of Capital (WACC) via CAPM.

    Cost of equity = risk_free + beta * equity_risk_premium      (CAPM)
    After-tax Kd   = pre_tax_cost_of_debt * (1 - tax_rate)
    Weights        = market value of equity vs net debt
    WACC           = Ke * We + Kd_after_tax * Wd

For a near-all-equity company (Netflix) the debt weight is tiny, so WACC
sits just below the cost of equity — exactly what we'd expect.
"""
from __future__ import annotations

from dataclasses import dataclass

from .data_loader import CompanySnapshot


@dataclass
class WaccResult:
    cost_of_equity: float
    after_tax_cost_of_debt: float
    equity_weight: float
    debt_weight: float
    wacc: float

    def describe(self) -> str:
        return (
            f"  Cost of equity (CAPM) : {self.cost_of_equity:6.2%}\n"
            f"  After-tax cost of debt: {self.after_tax_cost_of_debt:6.2%}\n"
            f"  Equity weight         : {self.equity_weight:6.2%}\n"
            f"  Debt weight           : {self.debt_weight:6.2%}\n"
            f"  WACC                  : {self.wacc:6.2%}"
        )


def compute_wacc(snap: CompanySnapshot, cfg: dict) -> WaccResult:
    w = cfg["wacc"]
    tax = cfg["tax_rate"]

    cost_of_equity = w["risk_free_rate"] + snap.beta * w["equity_risk_premium"]
    after_tax_kd = w["pre_tax_cost_of_debt"] * (1 - tax)

    # Market-value capital structure. Net debt can be negative (net cash);
    # we floor the debt weight at zero so a net-cash firm is treated as
    # all-equity rather than producing a nonsensical negative weight.
    equity_mv = snap.market_cap
    debt_mv = max(snap.net_debt, 0.0)
    total = equity_mv + debt_mv

    equity_weight = equity_mv / total
    debt_weight = debt_mv / total

    wacc = cost_of_equity * equity_weight + after_tax_kd * debt_weight
    return WaccResult(cost_of_equity, after_tax_kd, equity_weight, debt_weight, wacc)
