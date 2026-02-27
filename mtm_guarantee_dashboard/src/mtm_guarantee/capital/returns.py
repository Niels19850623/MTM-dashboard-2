from __future__ import annotations


def waterfall(
    notional: float,
    client_fee_bps: float,
    opex_bps: float,
    reserve_bps: float,
    expected_loss: float,
    mezz_notional: float,
    mezz_coupon_pct: float,
    senior_limit: float,
    senior_fee_bps: float,
    equity_capital: float,
    senior_capital_factor: float,
) -> dict:
    premium = notional * client_fee_bps / 10000
    opex = notional * opex_bps / 10000
    reserve = notional * reserve_bps / 10000
    net_available = premium - opex - reserve - expected_loss
    mezz_coupon = mezz_notional * mezz_coupon_pct
    senior_fee = senior_limit * senior_fee_bps / 10000
    equity_residual = net_available - mezz_coupon - senior_fee
    equity_roe = equity_residual / equity_capital if equity_capital > 0 else 0.0
    mezz_icr = net_available / mezz_coupon if mezz_coupon > 0 else 0.0
    senior_capital = senior_limit * senior_capital_factor
    senior_roe = senior_fee / senior_capital if senior_capital > 0 else 0.0
    return {
        "premium": premium,
        "opex": opex,
        "reserve": reserve,
        "expected_loss": expected_loss,
        "net_available": net_available,
        "mezz_coupon": mezz_coupon,
        "senior_fee": senior_fee,
        "equity_residual": equity_residual,
        "equity_roe": equity_roe,
        "equity_irr_proxy": equity_roe,
        "mezz_icr": mezz_icr,
        "senior_roe": senior_roe,
    }
