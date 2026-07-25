"""
Growth router — /api/growth/summary (§5).
Shows total recovered money and compounding projections.
"""
from fastapi import APIRouter, Depends
from bson import ObjectId
from app.database import get_database
from app.auth import get_current_user
from app.services.growth_simulator import simulate_growth, compute_monthly_chart_data
from app.config import settings

router = APIRouter(prefix="/api/growth", tags=["growth"])


@router.get("/summary")
async def get_growth_summary(
    db=Depends(get_database),
    current_user=Depends(get_current_user),
):
    """
    Total recovered amount and compounding projection at 1/3/5 years.
    Clearly labeled as an illustrative simulation, not investment advice.
    """
    user_id = ObjectId(str(current_user["_id"]))

    # Sum all money recovered from actions redirected to growth
    total_monthly_recovered = 0.0
    total_recovered = 0.0
    actions_count = 0

    async for action in db.actions.find({
        "user_id": user_id,
        "redirected_to_growth": True,
    }):
        total_recovered += action.get("money_recovered", 0)
        total_monthly_recovered += action.get("money_recovered", 0)
        actions_count += 1

    # Simulate growth projections
    projections = simulate_growth(
        monthly_contribution=total_monthly_recovered,
        annual_return_pct=settings.ASSUMED_ANNUAL_RETURN_PCT,
        years=[1, 3, 5],
    )

    # Monthly chart data for visualization
    chart_data = compute_monthly_chart_data(
        monthly_contribution=total_monthly_recovered,
        total_months=60,
        annual_return_pct=settings.ASSUMED_ANNUAL_RETURN_PCT,
    )

    return {
        "total_monthly_contribution": round(total_monthly_recovered, 2),
        "total_recovered_to_date": round(total_recovered, 2),
        "actions_count": actions_count,
        "assumed_annual_return_pct": settings.ASSUMED_ANNUAL_RETURN_PCT,
        "projections": projections,
        "chart_data": chart_data,
        "disclaimer": (
            "This is an illustrative simulation assuming a {:.0f}% annual return, "
            "compounded monthly. It is not investment advice and actual returns may vary."
        ).format(settings.ASSUMED_ANNUAL_RETURN_PCT),
    }
