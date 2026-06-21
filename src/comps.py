"""Comparable company ("comps") analysis.

Computes trading multiples for each peer, takes the peer-set median, then
applies those medians to the target's metrics to back into an implied
equity value per share. Multiples used:

    EV / Sales, EV / EBITDA, EV / EBIT   (enterprise-value based)
    P / E                                (equity based; skipped if NI <= 0)

Implied per share from an EV multiple:
    implied_EV     = multiple * target_metric
    implied_equity = implied_EV - target_net_debt
    per_share      = implied_equity / shares
Implied per share from P/E:
    per_share      = (multiple * target_net_income) / shares
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data_loader import CompanySnapshot, get_peer_tickers, get_snapshot


@dataclass
class CompsResult:
    peer_table: pd.DataFrame      # each peer's multiples
    median_multiples: dict        # median of each multiple across peers
    implied: pd.DataFrame         # implied value per share by method
    implied_mean: float           # simple average across methods
    current_price: float


def _multiples(snap: CompanySnapshot) -> dict:
    ev = snap.enterprise_value
    return {
        "ticker": snap.ticker,
        "ev_sales": ev / snap.revenue if snap.revenue else np.nan,
        "ev_ebitda": ev / snap.ebitda if snap.ebitda else np.nan,
        "ev_ebit": ev / snap.operating_income if snap.operating_income else np.nan,
        "pe": (snap.market_cap / snap.net_income) if snap.net_income > 0 else np.nan,
    }


def run_comps(target: str, db_path=None) -> CompsResult:
    kwargs = {"db_path": db_path} if db_path else {}
    target_snap = get_snapshot(target, **kwargs)
    peers = get_peer_tickers(target, **kwargs)

    peer_rows = [_multiples(get_snapshot(p, **kwargs)) for p in peers]
    peer_table = pd.DataFrame(peer_rows).set_index("ticker")

    median = {col: float(np.nanmedian(peer_table[col])) for col in peer_table.columns}

    # Apply peer medians to the target's own metrics.
    ev_from = {
        "EV/Sales": median["ev_sales"] * target_snap.revenue,
        "EV/EBITDA": median["ev_ebitda"] * target_snap.ebitda,
        "EV/EBIT": median["ev_ebit"] * target_snap.operating_income,
    }
    implied_rows = []
    for method, implied_ev in ev_from.items():
        equity = implied_ev - target_snap.net_debt
        implied_rows.append({
            "method": method,
            "peer_median_multiple": round(
                median[{"EV/Sales": "ev_sales", "EV/EBITDA": "ev_ebitda",
                        "EV/EBIT": "ev_ebit"}[method]], 1),
            "implied_value_per_share": equity / target_snap.shares_outstanding,
        })
    # P/E based
    implied_rows.append({
        "method": "P/E",
        "peer_median_multiple": round(median["pe"], 1),
        "implied_value_per_share":
            median["pe"] * target_snap.net_income / target_snap.shares_outstanding,
    })

    implied = pd.DataFrame(implied_rows)
    implied_mean = float(implied["implied_value_per_share"].mean())

    return CompsResult(
        peer_table=peer_table.round(1),
        median_multiples={k: round(v, 1) for k, v in median.items()},
        implied=implied,
        implied_mean=implied_mean,
        current_price=target_snap.price,
    )
