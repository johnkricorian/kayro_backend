from fastapi import APIRouter, Query

from app.services.score_engine import build_stock_score

router = APIRouter(
    prefix="/score",
    tags=["Score"]
)


@router.get("/{ticker}")
def get_score(
    ticker: str,
    forecast_horizon: int = Query(default=15, ge=1, le=60)
):
    return build_stock_score(ticker, forecast_horizon)
