from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from mtm_guarantee.config import DEFAULT_CURRENCIES
from mtm_guarantee.io.validation import validate_currency_subset


@dataclass
class WorkbookConfig:
    fx_sheet: str = "Historical_fx"
    rates_sheet_candidates: tuple[str, ...] = (
        "Interest_rates",
        "Rates",
        "historical_rates",
        "IR",
    )


def _parse_wide_sheet(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "currency"})
    date_cols = [c for c in df.columns if c != "currency"]
    melted = df.melt(id_vars=["currency"], value_vars=date_cols, var_name="date", value_name="value")
    melted["date"] = pd.to_datetime(melted["date"], errors="coerce")
    out = melted.dropna(subset=["date", "value"]).pivot(index="date", columns="currency", values="value")
    out = out.sort_index()
    return out


def load_workbook_data(excel_path: str | Path, config: WorkbookConfig | None = None) -> dict:
    cfg = config or WorkbookConfig()
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel workbook not found: {excel_path}")

    xls = pd.ExcelFile(excel_path)
    if cfg.fx_sheet not in xls.sheet_names:
        raise ValueError(f"Missing FX sheet '{cfg.fx_sheet}'. Available sheets: {xls.sheet_names}")

    fx_raw = pd.read_excel(excel_path, sheet_name=cfg.fx_sheet)
    fx = _parse_wide_sheet(fx_raw)
    present, missing = validate_currency_subset(fx)
    fx = fx[present].dropna(how="all")

    rates_sheet = next((s for s in cfg.rates_sheet_candidates if s in xls.sheet_names), None)
    if not rates_sheet:
        raise ValueError(
            f"No rates sheet found. Provide one of {cfg.rates_sheet_candidates}. Available: {xls.sheet_names}"
        )
    rates_raw = pd.read_excel(excel_path, sheet_name=rates_sheet)
    rates = _parse_wide_sheet(rates_raw)
    rate_cols = [c for c in DEFAULT_CURRENCIES if c in rates.columns]
    rates = rates[rate_cols].dropna(how="all")

    return {
        "fx": fx,
        "rates": rates,
        "missing_currencies": missing,
        "sheets": xls.sheet_names,
        "rates_sheet_used": rates_sheet,
    }
