from __future__ import annotations

import numpy as np
import pandas as pd

from mtm_guarantee.capital.returns import waterfall
from mtm_guarantee.guarantee.contract import GuaranteeContract
from mtm_guarantee.guarantee.payout import payout_default_triggered
from mtm_guarantee.io.excel_loader import WorkbookConfig, load_workbook_data
from mtm_guarantee.market.fx import normalize_quotes


def _sheet_df(currencies):
    dates = pd.date_range("2020-01-31", periods=6, freq="M")
    rows = []
    for c in currencies:
        row = {"currency": c}
        row.update({d: 100 + i for i, d in enumerate(dates)})
        rows.append(row)
    return pd.DataFrame(rows)


def test_loader_reads_fx_subset(tmp_path):
    ccys = ["UGX", "TZS", "KES", "BWP", "BDT", "LKR", "VND", "IDR"]
    fx = _sheet_df(ccys)
    rates = _sheet_df(ccys)
    p = tmp_path / "book.xlsx"
    with pd.ExcelWriter(p) as writer:
        fx.to_excel(writer, sheet_name="Historical_fx", index=False)
        rates.to_excel(writer, sheet_name="Interest_rates", index=False)
    out = load_workbook_data(p, WorkbookConfig())
    assert set(ccys).issubset(set(out["fx"].columns))


def test_quote_inversion_works():
    df = pd.DataFrame({"UGX": [1000.0, 1100.0]})
    inv = normalize_quotes(df, {"UGX": True})
    assert np.isclose(inv.iloc[0, 0], 1 / 1000.0)


def test_payout_sign_lender_positive_only():
    mtm = np.array([[10.0, -5.0], [-3.0, -1.0]])
    d = np.array([0.1, 0.1])
    c = GuaranteeContract()
    p = payout_default_triggered(mtm, d, 100.0, c)
    assert p[0] > 0 and p[1] == 0


def test_waterfall_balances():
    w = waterfall(100, 100, 10, 5, 1, 10, 0.1, 80, 50, 10, 0.2)
    lhs = w["net_available"] - w["mezz_coupon"] - w["senior_fee"]
    assert np.isclose(lhs, w["equity_residual"])
