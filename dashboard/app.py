"""Interactive valuation dashboard for the equity-valuation-framework.

Reads the same SQLite database and reuses the same DCF / WACC / comps engine
as the command-line tool (`run_valuation.py`) and the Excel model, so every
number stays consistent across all three layers.

Run locally:
    pip install -r requirements.txt
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import copy
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.build_db import DB_PATH, build  # noqa: E402
from src.comps import run_comps  # noqa: E402
from src.data_loader import get_history, get_snapshot  # noqa: E402
from src.dcf import run_all_scenarios, run_dcf  # noqa: E402
from src.wacc import compute_wacc  # noqa: E402

TARGET = "NFLX"
C = {  # palette
    "bear": "#c1485b", "base": "#2f6f9f", "bull": "#2a9d8f",
    "comps": "#8d99ae", "price": "#e76f51", "rev": "#2f6f9f",
    "fcf": "#2a9d8f", "grid": "#e6e9ef",
}

st.set_page_config(page_title="Equity Valuation — Netflix", layout="wide")


# ----------------------------------------------------------------- loaders
@st.cache_resource
def _db_ready() -> bool:
    if not DB_PATH.exists():
        build()
    return True


@st.cache_data
def load_config() -> dict:
    return yaml.safe_load((ROOT / "config" / "netflix.yaml").read_text())


@st.cache_data
def load_snapshot():
    return get_snapshot(TARGET)


@st.cache_data
def load_history() -> pd.DataFrame:
    return get_history(TARGET)


@st.cache_data
def load_kpis() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fiscal_year, metric, value, unit FROM operating_metrics WHERE ticker=?",
        con, params=(TARGET,),
    )
    con.close()
    return df


def sensitivity_grid(snap, cfg_base, scenario, waccs, tgs):
    z = []
    for w in waccs:
        row = []
        for g in tgs:
            c = copy.deepcopy(cfg_base)
            s = c["scenarios"][scenario]
            s["wacc_override"], s["terminal_growth_override"] = w, g
            try:
                row.append(run_dcf(snap, c, scenario).value_per_share)
            except ValueError:
                row.append(float("nan"))
        z.append(row)
    return z


# ----------------------------------------------------------------- compute
_db_ready()
cfg = load_config()
snap = load_snapshot()
hist = load_history().sort_values("fiscal_year")
kpis = load_kpis()
base_wacc = compute_wacc(snap, cfg).wacc
all_res = run_all_scenarios(snap, cfg)
comps = run_comps(TARGET)

# ---- sidebar: interactive DCF controls ----
st.sidebar.header("DCF controls")
scenario = st.sidebar.radio("Scenario", ["bear", "base", "bull"], index=1,
                            format_func=str.title)
scn = cfg["scenarios"][scenario]
d_wacc = (scn.get("wacc_override") or base_wacc) * 100
d_tg = (scn.get("terminal_growth_override") or cfg["terminal_growth_rate"]) * 100

wacc = st.sidebar.slider("WACC (%)", 6.0, 15.0, round(float(d_wacc), 2), 0.25) / 100
tg = st.sidebar.slider("Terminal growth (%)", 1.0, 5.0, round(float(d_tg), 2), 0.10) / 100
g_adj = st.sidebar.slider("Revenue-growth shift (ppt, all years)", -5.0, 5.0, 0.0, 0.5) / 100
m_adj = st.sidebar.slider("FCF-margin shift (ppt, all years)", -5.0, 5.0, 0.0, 0.5) / 100
st.sidebar.caption("Sliders re-run the DCF live. Defaults load from the selected "
                   "scenario in `config/netflix.yaml`.")

cfg_live = copy.deepcopy(cfg)
s = cfg_live["scenarios"][scenario]
s["wacc_override"], s["terminal_growth_override"] = wacc, tg
s["revenue_growth"] = [g + g_adj for g in scn["revenue_growth"]]
if cfg["fcf_method"] == "margin":
    s["fcf_margin"] = [min(max(m + m_adj, 0.0), 0.6) for m in scn["fcf_margin"]]
res = run_dcf(snap, cfg_live, scenario)

# ----------------------------------------------------------------- header
st.title("Netflix, Inc. (NFLX) — Equity Valuation Dashboard")
st.caption("DCF + comparable companies · base year FY2025 · driven by the same "
           "engine and database as the repo's Python tool and Excel model.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Reference price", f"${snap.price:,.2f}")
m2.metric(f"{scenario.title()} value/share (live)", f"${res.value_per_share:,.2f}",
          f"{res.upside_pct:+.1%} vs price")
m3.metric("Base-case value/share", f"${all_res['base'].value_per_share:,.2f}")
m4.metric("WACC (base)", f"{base_wacc:.2%}")

tab_val, tab_fin, tab_kpi, tab_comp = st.tabs(
    ["Valuation", "Financials", "Operating KPIs", "Comparables"])

# ============================================================== Valuation
with tab_val:
    left, right = st.columns([1.1, 1])

    with left:
        st.subheader("Valuation range")
        labels = ["Bear", "Comps", "Base", "Bull"]
        vals = [all_res["bear"].value_per_share, comps.implied_mean,
                all_res["base"].value_per_share, all_res["bull"].value_per_share]
        cols = [C["bear"], C["comps"], C["base"], C["bull"]]
        fig = go.Figure(go.Bar(
            x=vals, y=labels, orientation="h",
            marker_color=cols,
            text=[f"${v:,.0f}" for v in vals], textposition="outside"))
        fig.add_vline(x=snap.price, line_dash="dash", line_color=C["price"],
                      annotation_text=f"Price ${snap.price:,.0f}",
                      annotation_position="top")
        fig.update_layout(height=300, margin=dict(l=10, r=30, t=20, b=10),
                          xaxis_title="Value per share ($)",
                          plot_bgcolor="white", showlegend=False)
        fig.update_xaxes(gridcolor=C["grid"], zeroline=False)
        st.plotly_chart(fig, width='stretch')

        st.subheader(f"{scenario.title()}-case projection (live)")
        proj = res.projection
        f2 = go.Figure()
        f2.add_bar(x=proj["year"], y=proj["fcf"], name="Free cash flow",
                   marker_color=C["fcf"])
        f2.add_trace(go.Scatter(x=proj["year"], y=proj["revenue"], name="Revenue",
                                mode="lines+markers", line_color=C["rev"], yaxis="y2"))
        f2.update_layout(
            height=300, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white",
            yaxis=dict(title="FCF ($mm)", gridcolor=C["grid"]),
            yaxis2=dict(title="Revenue ($mm)", overlaying="y", side="right",
                        showgrid=False),
            legend=dict(orientation="h", y=1.15), xaxis=dict(tickformat="d"))
        st.plotly_chart(f2, width='stretch')

    with right:
        st.subheader("Enterprise → equity bridge (live)")
        b = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "total", "relative", "total"],
            x=["PV explicit FCF", "PV terminal value", "Enterprise value",
               "Less: net debt", "Equity value"],
            y=[res.pv_explicit, res.pv_terminal, None, -snap.net_debt, None],
            text=[f"${res.pv_explicit:,.0f}", f"${res.pv_terminal:,.0f}",
                  f"${res.enterprise_value:,.0f}", f"${-snap.net_debt:,.0f}",
                  f"${res.equity_value:,.0f}"],
            textposition="outside",
            connector={"line": {"color": C["grid"]}}))
        b.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10),
                        plot_bgcolor="white", showlegend=False)
        b.update_yaxes(gridcolor=C["grid"], title="$mm")
        st.plotly_chart(b, width='stretch')
        st.caption(f"Terminal value is {res.terminal_pct_of_ev:.0%} of enterprise "
                   f"value (healthy range ~50–75%).")

        st.subheader("Sensitivity: value/share")
        waccs = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
        tgs = [tg - 0.01, tg - 0.005, tg, tg + 0.005, tg + 0.01]
        z = sensitivity_grid(snap, cfg_live, scenario, waccs, tgs)
        hm = go.Figure(go.Heatmap(
            z=z, x=[f"{g:.1%}" for g in tgs], y=[f"{w:.1%}" for w in waccs],
            colorscale="RdYlGn", showscale=False,
            text=[[f"${v:,.0f}" for v in row] for row in z],
            texttemplate="%{text}", textfont={"size": 11}))
        hm.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                         xaxis_title="Terminal growth →", yaxis_title="WACC ↓")
        st.plotly_chart(hm, width='stretch')

# ============================================================== Financials
with tab_fin:
    h = hist.copy()
    h["gross_margin"] = h["gross_profit"] / h["revenue"]
    h["operating_margin"] = h["operating_income"] / h["revenue"]
    h["net_margin"] = h["net_income"] / h["revenue"]
    h["fcf_margin"] = h["free_cash_flow"] / h["revenue"]

    a, b = st.columns(2)
    with a:
        st.subheader("Revenue & operating income")
        f = go.Figure()
        f.add_bar(x=h["fiscal_year"], y=h["revenue"], name="Revenue",
                  marker_color=C["rev"])
        f.add_bar(x=h["fiscal_year"], y=h["operating_income"],
                  name="Operating income", marker_color=C["bull"])
        f.update_layout(barmode="group", height=320, plot_bgcolor="white",
                        margin=dict(l=10, r=10, t=20, b=10),
                        yaxis_title="$mm", legend=dict(orientation="h", y=1.15),
                        xaxis=dict(tickformat="d"))
        f.update_yaxes(gridcolor=C["grid"])
        st.plotly_chart(f, width='stretch')

        st.subheader("Operating vs free cash flow")
        f3 = go.Figure()
        f3.add_bar(x=h["fiscal_year"], y=h["operating_cash_flow"],
                   name="Operating CF", marker_color=C["base"])
        f3.add_bar(x=h["fiscal_year"], y=h["free_cash_flow"], name="Free CF",
                   marker_color=C["fcf"])
        f3.update_layout(barmode="group", height=320, plot_bgcolor="white",
                         margin=dict(l=10, r=10, t=20, b=10), yaxis_title="$mm",
                         legend=dict(orientation="h", y=1.15),
                         xaxis=dict(tickformat="d"))
        f3.update_yaxes(gridcolor=C["grid"])
        st.plotly_chart(f3, width='stretch')

    with b:
        st.subheader("Margin trends")
        f2 = go.Figure()
        for col, name, color in [
            ("gross_margin", "Gross", C["comps"]),
            ("operating_margin", "Operating", C["base"]),
            ("net_margin", "Net", C["bull"]),
            ("fcf_margin", "FCF", C["price"]),
        ]:
            f2.add_trace(go.Scatter(x=h["fiscal_year"], y=h[col], name=name,
                                    mode="lines+markers", line_color=color))
        f2.update_layout(height=320, plot_bgcolor="white",
                         margin=dict(l=10, r=10, t=20, b=10),
                         yaxis_tickformat=".0%", legend=dict(orientation="h", y=1.15),
                         xaxis=dict(tickformat="d"))
        f2.update_yaxes(gridcolor=C["grid"])
        st.plotly_chart(f2, width='stretch')

        st.subheader("Financials ($mm)")
        show = h[["fiscal_year", "revenue", "operating_income", "net_income",
                  "free_cash_flow"]].set_index("fiscal_year")
        st.dataframe(show.style.format("{:,.0f}"), width='stretch')

# ============================================================== KPIs
with tab_kpi:
    st.caption("Operating metrics from the database. Coverage here is illustrative "
               "and limited (mostly FY2024–25); refresh from filings to extend.")
    if kpis.empty:
        st.info("No operating metrics loaded for this company.")
    else:
        kp = kpis.pivot_table(index="fiscal_year", columns="metric", values="value")
        a, b = st.columns(2)
        with a:
            if "paid_memberships" in kp:
                st.subheader("Paid memberships (m)")
                mem = kp["paid_memberships"].dropna()
                f = go.Figure(go.Bar(x=mem.index, y=mem.values, marker_color=C["base"],
                                     text=[f"{v:,.0f}" for v in mem.values],
                                     textposition="outside"))
                f.update_layout(height=300, plot_bgcolor="white",
                                margin=dict(l=10, r=10, t=20, b=10),
                                xaxis=dict(tickformat="d"))
                f.update_yaxes(gridcolor=C["grid"])
                st.plotly_chart(f, width='stretch')
                # rough revenue-per-membership
                rev = hist.set_index("fiscal_year")["revenue"]
                arpu = (rev / mem).dropna()
                if not arpu.empty:
                    st.caption("Revenue per membership ($/yr): " +
                               ", ".join(f"{y}: ${v*1e6/1e6:,.0f}"  # $mm/m -> $
                                         for y, v in arpu.items()))
        with b:
            if "operating_margin" in kp:
                st.subheader("Operating margin (%)")
                om = kp["operating_margin"].dropna()
                f = go.Figure(go.Scatter(x=om.index, y=om.values,
                                         mode="lines+markers", line_color=C["bull"]))
                f.update_layout(height=300, plot_bgcolor="white",
                                margin=dict(l=10, r=10, t=20, b=10),
                                yaxis_ticksuffix="%", xaxis=dict(tickformat="d"))
                f.update_yaxes(gridcolor=C["grid"])
                st.plotly_chart(f, width='stretch')
            extra = [m for m in ("ad_revenue", "ucan_revenue_q4") if m in kp]
            if extra:
                latest = kp[extra].dropna(how="all").tail(1)
                for m in extra:
                    val = latest[m].iloc[0] if not latest.empty else None
                    if val is not None:
                        st.metric(m.replace("_", " ").title() + " ($mm)", f"{val:,.0f}")

# ============================================================== Comparables
with tab_comp:
    st.subheader("Peer trading multiples")
    pt = comps.peer_table.copy()
    # add NFLX's own multiples for context
    nflx_row = {
        "ev_sales": snap.enterprise_value / snap.revenue,
        "ev_ebitda": snap.enterprise_value / snap.ebitda,
        "ev_ebit": snap.enterprise_value / snap.operating_income,
        "pe": snap.market_cap / snap.net_income,
    }
    pt_disp = pd.concat([pd.DataFrame({k: [round(v, 1)] for k, v in nflx_row.items()},
                                      index=["NFLX"]), pt])
    st.dataframe(pt_disp.style.format("{:.1f}x", na_rep="n/m"),
                 width='stretch')

    a, b = st.columns(2)
    with a:
        st.subheader("EV / Sales — Netflix vs peers")
        ser = pt_disp["ev_sales"].dropna()
        colors = [C["price"] if i == "NFLX" else C["comps"] for i in ser.index]
        f = go.Figure(go.Bar(x=ser.index, y=ser.values, marker_color=colors,
                             text=[f"{v:.1f}x" for v in ser.values],
                             textposition="outside"))
        f.update_layout(height=320, plot_bgcolor="white",
                        margin=dict(l=10, r=10, t=20, b=10), yaxis_title="EV/Sales")
        f.update_yaxes(gridcolor=C["grid"])
        st.plotly_chart(f, width='stretch')
        st.caption("Netflix trades at a steep premium to legacy-media peers — a "
                   "premium its growth and margins have to justify.")
    with b:
        st.subheader("Implied value per share")
        imp = comps.implied.copy()
        imp.columns = ["Method", "Peer median", "Value/share ($)"]
        f = go.Figure(go.Bar(
            x=imp["Method"], y=imp["Value/share ($)"], marker_color=C["comps"],
            text=[f"${v:,.0f}" for v in imp["Value/share ($)"]],
            textposition="outside"))
        f.add_hline(y=snap.price, line_dash="dash", line_color=C["price"],
                    annotation_text=f"Price ${snap.price:,.0f}")
        f.update_layout(height=320, plot_bgcolor="white",
                        margin=dict(l=10, r=10, t=20, b=10), yaxis_title="$/share")
        f.update_yaxes(gridcolor=C["grid"])
        st.plotly_chart(f, width='stretch')
        st.caption(f"Average of methods: ${comps.implied_mean:,.2f}/share.")

# ----------------------------------------------------------------- footer
with st.expander("Caveats & methodology"):
    for note in cfg.get("notes", []):
        st.markdown(f"- {note}")
    st.markdown(
        "- DCF uses the FCF-margin method (appropriate for content-spend businesses), "
        "mid-year discounting and a Gordon-growth terminal value.\n"
        "- The dashboard, the Python tool and the Excel model all read the same "
        "config and database, so their numbers reconcile.\n"
        "- **Educational / portfolio use only. Not investment advice.**")
