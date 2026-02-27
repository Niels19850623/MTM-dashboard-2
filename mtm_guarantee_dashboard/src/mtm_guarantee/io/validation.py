from __future__ import annotations

import pandas as pd

from mtm_guarantee.config import DEFAULT_CURRENCIES


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    clean = {k: max(float(v), 0.0) for k, v in weights.items()}
    total = sum(clean.values())
    if total <= 0:
        return {k: 1.0 / len(clean) for k in clean} if clean else {}
    return {k: v / total for k, v in clean.items()}


def validate_currency_subset(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    present = [c for c in DEFAULT_CURRENCIES if c in df.columns]
    missing = [c for c in DEFAULT_CURRENCIES if c not in df.columns]
    return present, missing
