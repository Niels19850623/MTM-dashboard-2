from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_quotes(fx_df: pd.DataFrame, inversion: dict[str, bool]) -> pd.DataFrame:
    out = fx_df.copy()
    for ccy, invert in inversion.items():
        if invert and ccy in out.columns:
            out[ccy] = 1.0 / out[ccy].replace(0, np.nan)
    return out


def monthly_returns(fx_df: pd.DataFrame) -> pd.DataFrame:
    m = fx_df.resample("M").last().ffill()
    return np.log(m / m.shift(1)).dropna(how="all")
