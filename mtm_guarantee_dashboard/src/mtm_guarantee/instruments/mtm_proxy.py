from __future__ import annotations

import numpy as np


def mtm_phase0(s0: np.ndarray, st: np.ndarray, notionals: np.ndarray) -> np.ndarray:
    rel = np.maximum(s0 / st - 1.0, 0.0)
    return notionals * rel


def mtm_phase1(
    s0: np.ndarray,
    st: np.ndarray,
    notionals: np.ndarray,
    carry: np.ndarray,
    ccs_share: float,
    ndf_share: float,
) -> np.ndarray:
    fx_component = np.maximum(s0 / st - 1.0, 0.0)
    ccs = fx_component + np.maximum(carry, -0.1)
    ndf = fx_component + 0.5 * np.maximum(carry, -0.1)
    return notionals * (ccs_share * ccs + ndf_share * ndf)
