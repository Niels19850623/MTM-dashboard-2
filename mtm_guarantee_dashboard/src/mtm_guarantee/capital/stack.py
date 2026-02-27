from __future__ import annotations


def capital_stack(notional: float, equity_pct: float, mezz_pct: float, senior_pct: float) -> dict:
    return {
        "equity": notional * equity_pct,
        "mezz": notional * mezz_pct,
        "senior": notional * senior_pct,
    }
