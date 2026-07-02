from fastapi import APIRouter

from app.database.prediction_repository import get_predictions

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


@router.get("")
def predictions(limit: int = 100):
    rows = get_predictions(limit)

    return [
        {
            "id": row.id,
            "ticker": row.ticker,
            "created_at": row.created_at,
            "forecast_horizon": row.forecast_horizon,
            "direction": row.predicted_direction,
            "probability_up": row.probability_up,
            "confidence": row.confidence,
            "kayro_score": row.kayro_score,
            "recommendation": row.recommendation,
            "price_at_prediction": row.price_at_prediction,
            "price_after_horizon": row.price_after_horizon,
            "prediction_correct": row.prediction_correct,
            "evaluated_at": row.evaluated_at
        }
        for row in rows
    ]
