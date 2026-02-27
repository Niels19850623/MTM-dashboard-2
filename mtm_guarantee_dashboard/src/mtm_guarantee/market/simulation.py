from __future__ import annotations

import numpy as np
import pandas as pd

from mtm_guarantee.market.correlations import stressed_corr


def simulate_fx_paths(
    fx_history: pd.DataFrame,
    tenor_years: int,
    n_paths: int,
    mode: str,
    vol_multiplier: float = 1.0,
    corr_stress: float = 1.0,
    random_state: int = 42,
) -> tuple[np.ndarray, list[str]]:
    rng = np.random.default_rng(random_state)
    rets = np.log(fx_history.resample("M").last().ffill() / fx_history.resample("M").last().ffill().shift(1)).dropna()
    currencies = list(rets.columns)
    n_steps = int(12 * tenor_years)
    s0 = fx_history.iloc[-1][currencies].values

    if mode == "parametric_mc":
        mu = rets.mean().values
        cov = (rets.cov().values * vol_multiplier**2)
        corr = stressed_corr(rets, corr_stress).values
        vols = np.sqrt(np.diag(cov))
        cov = np.outer(vols, vols) * corr
        draws = rng.multivariate_normal(mu, cov, size=(n_paths, n_steps))
    else:
        idx = rng.integers(0, len(rets), size=(n_paths, n_steps))
        draws = rets.values[idx, :]

    log_paths = np.cumsum(draws, axis=1)
    paths = s0[None, None, :] * np.exp(log_paths)
    return paths, currencies
