from fastapi import APIRouter

from app.services.qeyro_score import build_qeyro_score

router = APIRouter(
    prefix="/kayro-score",
    tags=["Kayro Score"],
)


@router.get("/{ticker}")
def get_kayro_score(
    ticker: str,
    forecast_horizon: int = 15
):
    return build_qeyro_score(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
    )
