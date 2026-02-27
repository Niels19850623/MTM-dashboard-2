from __future__ import annotations

import numpy as np


def risk_metrics(losses: np.ndarray, confidence: float = 0.995, method: str = "ES") -> dict:
    losses = np.asarray(losses)
    q = np.quantile(losses, confidence)
    tail = losses[losses >= q]
    es = tail.mean() if len(tail) else q
    return {
        "EL": float(losses.mean()),
        "VaR": float(q),
        "ES": float(es),
        "confidence": confidence,
        "method": method,
    }


def exceedance_curve(losses: np.ndarray, points: int = 50) -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(0, np.max(losses), points)
    y = np.array([(losses > xi).mean() for xi in x])
    return x, y
