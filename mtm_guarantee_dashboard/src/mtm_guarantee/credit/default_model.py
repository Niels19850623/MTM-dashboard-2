from __future__ import annotations

import numpy as np


def draw_default_times(pd_annual: float, tenor_years: int, n_paths: int, rng: np.random.Generator) -> np.ndarray:
    hazard = -np.log(max(1 - pd_annual, 1e-8))
    u = rng.random(n_paths)
    t = -np.log(1 - u) / max(hazard, 1e-9)
    t[t > tenor_years] = np.nan
    return t


def piecewise_default_times(pd_annual: float, tenor_years: int, n_paths: int, rng: np.random.Generator) -> np.ndarray:
    years = np.arange(1, tenor_years + 1)
    annual_pd = np.clip(pd_annual * (1 + 0.05 * (years - 1)), 0, 0.5)
    t = np.full(n_paths, np.nan)
    u = rng.random((n_paths, tenor_years))
    alive = np.ones(n_paths, dtype=bool)
    for y in range(tenor_years):
        hit = alive & (u[:, y] < annual_pd[y])
        t[hit] = y + rng.random(np.sum(hit))
        alive[hit] = False
    return t
