from __future__ import annotations

import numpy as np
import pandas as pd


def stressed_corr(ret: pd.DataFrame, stress: float = 1.0) -> pd.DataFrame:
    corr = ret.corr().fillna(0.0)
    if stress == 1.0:
        return corr
    eye = np.eye(len(corr))
    stressed = eye + stress * (corr.values - eye)
    stressed = np.clip(stressed, -0.99, 0.99)
    np.fill_diagonal(stressed, 1.0)
    return pd.DataFrame(stressed, index=corr.index, columns=corr.columns)
