from __future__ import annotations

import numpy as np


def ndf_forward_adjustment(local_rate: np.ndarray, usd_rate: float = 0.03) -> np.ndarray:
    return 0.5 * (local_rate - usd_rate) / 12.0
