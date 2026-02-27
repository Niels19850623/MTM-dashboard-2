from __future__ import annotations

import numpy as np


def liquidity_metrics(
    payout_paths: np.ndarray,
    settlement_lag_days: int,
    dispute_delay_factor: float,
    floor_pct: float,
    notional: float,
) -> dict:
    lag_months = max(int(round((settlement_lag_days * dispute_delay_factor) / 30)), 1)
    shifted = np.roll(payout_paths, lag_months, axis=1)
    shifted[:, :lag_months] = 0.0
    monthly_calls = shifted.sum(axis=0)
    one_m = monthly_calls
    three_m = np.convolve(monthly_calls, np.ones(3), mode="same")
    p95_1m, p99_1m = np.quantile(one_m, [0.95, 0.99])
    p95_3m, p99_3m = np.quantile(three_m, [0.95, 0.99])
    rec = max(p99_1m, p99_3m / 3, floor_pct * notional)
    return {
        "monthly_calls": monthly_calls,
        "p95_1m": p95_1m,
        "p99_1m": p99_1m,
        "p95_3m": p95_3m,
        "p99_3m": p99_3m,
        "recommended_buffer": rec,
    }
