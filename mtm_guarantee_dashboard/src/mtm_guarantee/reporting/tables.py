from __future__ import annotations

import pandas as pd


def scenario_summary_table(scenario: dict) -> pd.DataFrame:
    rows = [{"parameter": k, "value": v} for k, v in scenario.items() if k != "weights"]
    return pd.DataFrame(rows)
