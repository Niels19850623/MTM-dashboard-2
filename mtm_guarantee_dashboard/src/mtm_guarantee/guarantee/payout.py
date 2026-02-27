from __future__ import annotations

import numpy as np

from mtm_guarantee.guarantee.contract import GuaranteeContract


def apply_structure(loss: np.ndarray, notional: float, contract: GuaranteeContract) -> np.ndarray:
    attach = contract.attachment * notional
    detach = contract.detachment * notional
    limited = np.minimum(np.maximum(loss - attach, 0.0), max(detach - attach, 0.0))
    limited = np.minimum(limited, contract.limit_pct * notional)
    return limited * contract.coverage_pct


def payout_default_triggered(
    mtm_paths: np.ndarray,
    default_times: np.ndarray,
    notional: float,
    contract: GuaranteeContract,
    lgd: float = 1.0,
) -> np.ndarray:
    n_steps = mtm_paths.shape[1]
    step_idx = np.clip((default_times * 12).astype(float), 0, n_steps - 1)
    payout = np.zeros(len(default_times))
    valid = ~np.isnan(default_times)
    idx = step_idx[valid].astype(int)
    mtm_at_default = np.maximum(mtm_paths[valid, idx], 0.0) * lgd
    payout[valid] = apply_structure(mtm_at_default, notional, contract)
    return payout


def payout_full_mtm(mtm_paths: np.ndarray, notional: float, contract: GuaranteeContract) -> np.ndarray:
    max_mtm = np.maximum(mtm_paths.max(axis=1), 0.0)
    return apply_structure(max_mtm, notional, contract)
