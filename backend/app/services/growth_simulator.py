"""
Growth simulator — compounding projection math (§6).
Treats recovered money as recurring monthly contributions.
Clearly labeled as an illustrative simulation, not investment advice.
"""
from app.config import settings


def simulate_growth(
    monthly_contribution: float,
    annual_return_pct: float = None,
    years: list[int] = None,
) -> list[dict]:
    """
    Project compounding growth of monthly contributions.

    Args:
        monthly_contribution: Amount redirected per month (sum of recovered money / 12).
        annual_return_pct: Assumed annual return (default from settings).
        years: List of year milestones to compute (default: [1, 3, 5]).

    Returns list of:
    {
        "years": int,
        "total_contributed": float,
        "projected_value": float,
        "growth_amount": float,
    }
    """
    if annual_return_pct is None:
        annual_return_pct = settings.ASSUMED_ANNUAL_RETURN_PCT

    if years is None:
        years = [1, 3, 5]

    monthly_rate = (annual_return_pct / 100) / 12
    results = []

    for y in years:
        n_months = y * 12
        total_contributed = monthly_contribution * n_months

        if monthly_rate > 0:
            # Future value of annuity formula
            fv = monthly_contribution * (((1 + monthly_rate) ** n_months - 1) / monthly_rate)
        else:
            fv = total_contributed

        results.append({
            "years": y,
            "total_contributed": round(total_contributed, 2),
            "projected_value": round(fv, 2),
            "growth_amount": round(fv - total_contributed, 2),
        })

    return results


def compute_monthly_chart_data(
    monthly_contribution: float,
    total_months: int = 60,  # 5 years
    annual_return_pct: float = None,
) -> list[dict]:
    """
    Generate month-by-month chart data for the growth visualization.

    Returns list of:
    {
        "month": int,
        "contributed": float,
        "projected_value": float,
    }
    """
    if annual_return_pct is None:
        annual_return_pct = settings.ASSUMED_ANNUAL_RETURN_PCT

    monthly_rate = (annual_return_pct / 100) / 12
    data = []
    balance = 0.0

    for month in range(1, total_months + 1):
        balance = (balance + monthly_contribution) * (1 + monthly_rate)
        data.append({
            "month": month,
            "contributed": round(monthly_contribution * month, 2),
            "projected_value": round(balance, 2),
        })

    return data
