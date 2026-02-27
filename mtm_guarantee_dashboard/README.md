# mtm_guarantee_dashboard

Production-style Python package and Streamlit app for modelling an EM FX hedging MTM guarantee vehicle.

## What this model does
- Ingests FX/rates history from Excel workbook (`FX Data and Interest rates.xlsx`).
- Restricts currency universe to: `UGX,TZS,KES,BWP,BDT,LKR,VND,IDR`.
- Simulates FX paths (historical bootstrap or parametric MC).
- Computes hedge MTM proxy (Phase 0 FX-only and Phase 1 carry-enhanced CCS/NDF mix).
- Applies guarantee contract logic in lender perspective (positive MTM to lender can trigger payout).
- Produces payout/loss distribution, EL, VaR/ES, required capital, max leverage.
- Runs investor return waterfall for equity/mezz/senior layer.
- Estimates liquidity buffer from monthly cash call distribution.

## What this model does not do
- It is **not** a full legal/ISDA valuation engine.
- CCS/NDF marking is intentionally proxy-based and dashboard-friendly.

## Install & run
```bash
pip install -e .
streamlit run app.py -- --excel "./FX Data and Interest rates.xlsx"
```

## Excel mapping config
Default mapping in `src/mtm_guarantee/io/excel_loader.py`:
- FX sheet: `Historical_fx`
- Rates sheet candidates: `Interest_rates`, `Rates`, `historical_rates`, `IR`

Expected layout for both sheets:
- first column = currency code
- remaining columns = date columns
- values = FX levels (LCY per USD by default) or interest rates

If sheet names differ, edit `WorkbookConfig`.

## Capital rule
- Compute loss metric from payout distribution (`VaR` or `ES` at confidence level).
- Required capital = metric × (1 + overlays).
- Max leverage = portfolio notional / required capital.

## Investor waterfall
Per year:
1. premium income
2. minus opex
3. minus reserve build
4. minus expected/simulated loss
5. minus mezz coupon
6. minus senior fee
7. residual to equity

Outputs include equity ROE/IRR proxy, mezz coverage ratio, senior implied ROE.

## Exports
- Scenario output CSV via dashboard download button.
- Tear sheet markdown saved to `outputs/tear_sheet.md`.

## Tests
```bash
pytest
```
