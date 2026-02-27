from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def leverage_roe_curve(leverage_grid: np.ndarray, base_return: float, selected: float):
    roe = base_return * leverage_grid
    fig = go.Figure()
    fig.add_scatter(x=leverage_grid, y=roe, mode="lines", name="Equity ROE")
    fig.add_vline(x=selected, line_dash="dash", annotation_text="Selected")
    return fig


def loss_exceedance_chart(x: np.ndarray, y: np.ndarray):
    return px.line(x=x, y=y, labels={"x": "Loss ($)", "y": "P(Loss>x)"}, title="Loss Exceedance")


def waterfall_chart(wf: dict):
    x = ["Premium", "Opex", "Reserve", "EL", "Mezz", "Senior Fee", "Equity"]
    y = [wf["premium"], -wf["opex"], -wf["reserve"], -wf["expected_loss"], -wf["mezz_coupon"], -wf["senior_fee"], wf["equity_residual"]]
    return go.Figure(go.Waterfall(x=x, y=y))


def risk_contrib_bar(contrib: dict):
    return px.bar(x=list(contrib.keys()), y=list(contrib.values()), labels={"x": "Currency", "y": "Contribution"})
