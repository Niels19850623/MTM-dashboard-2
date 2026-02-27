from __future__ import annotations

import numpy as np


def adjust_pd_with_fx(pd_base: float, fx_shock: np.ndarray, beta: float) -> np.ndarray:
    stressed = pd_base * np.exp(beta * fx_shock)
    return np.clip(stressed, 0.0001, 0.95)
