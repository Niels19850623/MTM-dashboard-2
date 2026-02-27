from __future__ import annotations


def required_capital(metric_value: float, overlay_pct: float) -> float:
    return metric_value * (1 + overlay_pct)
