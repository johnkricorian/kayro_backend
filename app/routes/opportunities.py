from fastapi import APIRouter, Query

from app.services.opportunity_service import get_opportunities

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"]
)


@router.get("")
def opportunities(
    sectors: list[str] = Query(default=["technology"]),
    limit: int = Query(default=20, ge=1, le=100),
    forecast_horizon: int = Query(default=15)
):
    return get_opportunities(
        sectors=sectors,
        limit=limit,
        forecast_horizon=forecast_horizon
    )
