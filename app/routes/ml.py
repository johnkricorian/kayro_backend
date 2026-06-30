from fastapi import APIRouter, Query
from app.services.ml_prediction import train_and_predict

router = APIRouter(
    prefix="/ml",
    tags=["ML Prediction"]
)


@router.get("/predict/{ticker}")
def predict_stock(
    ticker: str,
    forecast_horizon: int = Query(default=4, ge=1, le=30)
):
    return train_and_predict(
        ticker=ticker,
        forecast_horizon=forecast_horizon
    )
