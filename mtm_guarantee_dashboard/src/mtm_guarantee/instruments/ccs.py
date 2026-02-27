from __future__ import annotations

import numpy as np


def ccs_carry_adjustment(local_rate: np.ndarray, usd_rate: float = 0.03) -> np.ndarray:
    return (local_rate - usd_rate) / 12.0
