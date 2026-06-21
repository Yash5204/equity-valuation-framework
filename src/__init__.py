"""Equity valuation framework — DCF + comparable company analysis.

A small, config-driven toolkit that values any company from financials
held in a SQLite database. Demonstrated on Netflix (NFLX) but built to be
pointed at any ticker by swapping the config file and seeding the data.
"""
from .wacc import compute_wacc
from .dcf import run_dcf
from .comps import run_comps

__all__ = ["compute_wacc", "run_dcf", "run_comps"]
