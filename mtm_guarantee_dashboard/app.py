from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from mtm_guarantee.capital.liquidity import liquidity_metrics
from mtm_guarantee.capital.loss_dist import exceedance_curve, risk_metrics
from mtm_guarantee.capital.rating_capital import required_capital
from mtm_guarantee.capital.returns import waterfall
from mtm_guarantee.config import DEFAULT_CURRENCIES, default_scenario
from mtm_guarantee.credit.default_model import draw_default_times, piecewise_default_times
from mtm_guarantee.guarantee.contract import GuaranteeContract
from mtm_guarantee.guarantee.payout import payout_default_triggered, payout_full_mtm
from mtm_guarantee.instruments.mtm_proxy import mtm_phase0, mtm_phase1
from mtm_guarantee.io.excel_loader import load_workbook_data
from mtm_guarantee.io.validation import normalize_weights
from mtm_guarantee.market.fx import normalize_quotes
from mtm_guarantee.market.simulation import simulate_fx_paths
from mtm_guarantee.reporting.charts import leverage_roe_curve, loss_exceedance_chart, risk_contrib_bar, waterfall_chart
from mtm_guarantee.reporting.tables import scenario_summary_table
from mtm_guarantee.reporting.tearsheet import save_tearsheet


@st.cache_data
def load_data(path: str):
    return load_workbook_data(path)


@st.cache_data
def run_model(scenario: dict, fx_df: pd.DataFrame, rates_df: pd.DataFrame):
    fx_norm = normalize_quotes(fx_df, scenario["quote_inversion"])
    selected = scenario["currencies"]
    weights = normalize_weights({k: v for k, v in scenario["weights"].items() if k in selected})
    w_vec = np.array([weights[c] for c in selected])
    notional_ccy = scenario["notional_usd"] * w_vec

    paths, currencies = simulate_fx_paths(
        fx_norm[selected], scenario["tenor_years"], scenario["n_paths"], scenario["simulation_mode"], scenario["vol_multiplier"], scenario["stress_correlation"]
    )
    cidx = [currencies.index(c) for c in selected]
    paths = paths[:, :, cidx]
    s0 = fx_norm[selected].iloc[-1].values

    if scenario["mtm_phase"] == "phase0":
        mtm_ccy = mtm_phase0(s0[None, None, :], paths, notional_ccy[None, None, :])
    else:
        carry = np.zeros_like(paths)
        if not rates_df.empty:
            carry_level = (rates_df[selected].ffill().iloc[-1].values / 100 - 0.03) / 12
            carry = np.broadcast_to(carry_level[None, None, :], paths.shape)
        mtm_ccy = mtm_phase1(s0[None, None, :], paths, notional_ccy[None, None, :], carry, scenario["ccs_share"], scenario["ndf_share"])
    mtm_port = mtm_ccy.sum(axis=2)

    rng = np.random.default_rng(123)
    if scenario["default_model"] == "piecewise_hazard":
        default_t = piecewise_default_times(scenario["pd_annual"], scenario["tenor_years"], scenario["n_paths"], rng)
    else:
        default_t = draw_default_times(scenario["pd_annual"], scenario["tenor_years"], scenario["n_paths"], rng)

    contract = GuaranteeContract(
        coverage_pct=scenario["coverage_pct"],
        attachment=scenario["attachment"],
        detachment=scenario["detachment"],
        limit_pct=scenario["limit_pct"],
        mode=scenario["guarantee_mode"],
    )
    if scenario["guarantee_mode"] == "full_mtm":
        payouts = payout_full_mtm(mtm_port, scenario["notional_usd"], contract)
    else:
        payouts = payout_default_triggered(mtm_port, default_t, scenario["notional_usd"], contract, scenario["lgd"])

    risk = risk_metrics(payouts, scenario["confidence"], scenario["capital_method"])
    metric = risk[scenario["capital_method"]]
    req_cap = required_capital(metric, scenario["overlay_pct"])
    max_lev = scenario["notional_usd"] / req_cap if req_cap > 0 else np.nan

    contrib = {}
    for i, c in enumerate(selected):
        c_loss = np.maximum(mtm_ccy[:, :, i].max(axis=1), 0) * scenario["pd_annual"] * scenario["lgd"]
        contrib[c] = float(c_loss.mean())

    payout_paths = np.zeros((scenario["n_paths"], scenario["tenor_years"] * 12))
    if scenario["guarantee_mode"] == "default_triggered":
        for i, t in enumerate(default_t):
            if not np.isnan(t):
                m = min(int(t * 12), payout_paths.shape[1] - 1)
                payout_paths[i, m] = payouts[i]
    else:
        payout_paths[:, -1] = payouts

    liq = liquidity_metrics(
        payout_paths,
        scenario["settlement_lag_days"],
        scenario["dispute_delay_factor"],
        scenario["liquidity_floor_pct"],
        scenario["notional_usd"],
    )

    wf = waterfall(
        scenario["notional_usd"],
        scenario["client_fee_bps"],
        scenario["opex_bps"],
        scenario["reserve_bps"],
        risk["EL"],
        scenario["mezz_pct"] * scenario["notional_usd"],
        scenario["mezz_coupon_pct"],
        scenario["senior_limit_pct"] * scenario["notional_usd"],
        scenario["senior_fee_bps"],
        scenario["equity_pct"] * scenario["notional_usd"],
        scenario["senior_capital_factor"],
    )

    x_exc, y_exc = exceedance_curve(payouts)
    return {
        "payouts": payouts,
        "risk": risk,
        "required_capital": req_cap,
        "max_leverage": max_lev,
        "contrib": contrib,
        "waterfall": wf,
        "exceedance": (x_exc, y_exc),
        "liquidity": liq,
        "guarantee_hit_count": int(np.sum(payouts > 0)),
    }


def main(excel_default: str):
    st.set_page_config(layout="wide", page_title="MTM Guarantee Dashboard")
    st.title("MTM Guarantee Dashboard")
    scenario = default_scenario()

    with st.sidebar:
        st.header("Global Settings")
        excel_path = st.text_input("Excel path", value=excel_default)
        data = load_data(excel_path)
        if data["missing_currencies"]:
            st.warning(f"Missing currencies: {', '.join(data['missing_currencies'])}. Drop missing names in selection.")
        scenario["currencies"] = st.multiselect("Currencies", options=DEFAULT_CURRENCIES, default=[c for c in DEFAULT_CURRENCIES if c in data["fx"].columns])
        fast = st.toggle("Fast mode (2k paths)", value=False)
        scenario["n_paths"] = 2_000 if fast else st.number_input("Simulation paths", value=10_000, step=1000)
        scenario["simulation_mode"] = st.selectbox("Simulation mode", ["historical_bootstrap", "parametric_mc"])
        scenario["target_leverage"] = st.slider("Target leverage", 5.0, 20.0, 15.0, 0.5)
        run = st.button("Run simulation", type="primary")

    if not run:
        st.info("Set assumptions and click Run simulation")
        return

    tabs = st.tabs(["Portfolio Builder", "Risk & Capital", "Investor Returns", "Scenarios & Sensitivities", "Liquidity"])

    with tabs[0]:
        st.subheader("Portfolio Builder")
        ccy = scenario["currencies"]
        if not ccy:
            st.error("Select at least one currency")
            return
        wt_df = pd.DataFrame({"currency": ccy, "weight": [1/len(ccy)] * len(ccy)})
        wt_df = st.data_editor(wt_df, num_rows="fixed", use_container_width=True)
        if st.button("Equal weight"):
            wt_df["weight"] = 1 / len(ccy)
        scenario["weights"] = normalize_weights(dict(zip(wt_df["currency"], wt_df["weight"])))
        c1, c2, c3 = st.columns(3)
        scenario["notional_usd"] = c1.number_input("Total notional (USD)", value=100_000_000, step=10_000_000)
        scenario["tenor_years"] = c2.selectbox("Tenor", [3, 5, 7], index=1)
        scenario["mtm_phase"] = c3.selectbox("MTM engine", ["phase0", "phase1"], index=1)
        m1, m2 = st.columns(2)
        scenario["ccs_share"] = m1.slider("CCS %", 0.0, 1.0, 0.8)
        scenario["ndf_share"] = 1 - scenario["ccs_share"]
        m2.metric("NDF %", f"{scenario['ndf_share']:.0%}")
        model = run_model(scenario, data["fx"], data["rates"])
        st.dataframe(pd.DataFrame([scenario["weights"]]), use_container_width=True)

    with tabs[1]:
        st.subheader("Risk & Capital")
        r = model["risk"]
        a, b, c = st.columns(3)
        a.metric("Expected Loss", f"${r['EL']:,.0f}")
        b.metric("VaR", f"${r['VaR']:,.0f}")
        c.metric("ES", f"${r['ES']:,.0f}")
        d, e, f = st.columns(3)
        d.metric("Required Capital", f"${model['required_capital']:,.0f}")
        e.metric("Max leverage", f"{model['max_leverage']:.2f}x")
        f.metric("Guarantee hits", f"{model['guarantee_hit_count']}")
        x, y = model["exceedance"]
        st.plotly_chart(loss_exceedance_chart(x, y), use_container_width=True)
        st.plotly_chart(risk_contrib_bar(model["contrib"]), use_container_width=True)

    with tabs[2]:
        st.subheader("Investor Returns")
        wf = model["waterfall"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Equity ROE", f"{wf['equity_roe']:.2%}")
        c2.metric("Mezz ICR", f"{wf['mezz_icr']:.2f}x")
        c3.metric("Senior ROE", f"{wf['senior_roe']:.2%}")
        st.plotly_chart(waterfall_chart(wf), use_container_width=True)
        leverages = np.linspace(5, 20, 20)
        base = max(wf["equity_roe"] / max(scenario["target_leverage"], 1e-6), 0)
        st.plotly_chart(leverage_roe_curve(leverages, base, scenario["target_leverage"]), use_container_width=True)

    with tabs[3]:
        st.subheader("Scenarios & Sensitivities")
        pd_grid = np.linspace(0.01, 0.08, 8)
        vol_grid = np.linspace(0.8, 1.5, 8)
        hm = np.zeros((len(pd_grid), len(vol_grid)))
        for i, pdv in enumerate(pd_grid):
            for j, volm in enumerate(vol_grid):
                hm[i, j] = model["required_capital"] * (pdv / scenario["pd_annual"]) * volm
        hdf = pd.DataFrame(hm, index=np.round(pd_grid, 3), columns=np.round(vol_grid, 2))
        st.plotly_chart(px.imshow(hdf, labels=dict(x="Vol multiplier", y="PD", color="Req cap"), aspect="auto"), use_container_width=True)

    with tabs[4]:
        st.subheader("Liquidity")
        liq = model["liquidity"]
        st.metric("Recommended buffer", f"${liq['recommended_buffer']:,.0f}")
        st.plotly_chart(px.histogram(liq["monthly_calls"], nbins=30, title="Monthly cash calls"), use_container_width=True)
        st.dataframe(
            pd.DataFrame(
                {
                    "window": ["1M p95", "1M p99", "3M p95", "3M p99"],
                    "value": [liq["p95_1m"], liq["p99_1m"], liq["p95_3m"], liq["p99_3m"]],
                }
            ),
            use_container_width=True,
        )

    summary = scenario_summary_table(scenario)
    st.subheader("Scenario Summary")
    st.dataframe(summary, use_container_width=True)
    csv = pd.DataFrame({"payout": model["payouts"]}).to_csv(index=False)
    st.download_button("Download scenario outputs CSV", data=csv, file_name="scenario_outputs.csv", mime="text/csv")
    tear_md = f"# MTM Guarantee Tear Sheet\n\nRequired capital: ${model['required_capital']:,.0f}\n\nMax leverage: {model['max_leverage']:.2f}x\n"
    out_path = save_tearsheet("outputs/tear_sheet.md", tear_md)
    st.success(f"Tear sheet saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--excel", default="./FX Data and Interest rates.xlsx")
    args, _ = parser.parse_known_args()
    main(args.excel)
