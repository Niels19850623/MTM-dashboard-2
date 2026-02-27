from __future__ import annotations

import pandas as pd


def monthly_carry(rates_df: pd.DataFrame, usd_rate: float = 0.03) -> pd.DataFrame:
    monthly = rates_df.resample("M").last().ffill() / 100.0
    return (monthly - usd_rate) / 12.0
