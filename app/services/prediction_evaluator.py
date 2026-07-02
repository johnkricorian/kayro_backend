from datetime import datetime, timedelta

from app.database.prediction_repository import (
    get_pending_predictions,
    update_prediction_result
)
from app.services.market import fetch_market_data


def evaluate_pending_predictions() -> dict:
    predictions = get_pending_predictions()

    evaluated = 0
    skipped = 0
    errors = []

    for prediction in predictions:
        due_date = prediction.created_at + timedelta(
            days=prediction.forecast_horizon
        )

        if datetime.utcnow() < due_date:
            skipped += 1
            continue

        try:
            current_price = get_latest_price(prediction.ticker)

            prediction_correct = is_prediction_correct(
                predicted_direction=prediction.predicted_direction,
                start_price=prediction.price_at_prediction,
                end_price=current_price
            )

            update_prediction_result(
                prediction_id=prediction.id,
                price_after_horizon=current_price,
                prediction_correct=prediction_correct
            )

            evaluated += 1

        except Exception as error:
            errors.append({
                "prediction_id": prediction.id,
                "ticker": prediction.ticker,
                "error": str(error)
            })

    return {
        "pending": len(predictions),
        "evaluated": evaluated,
        "skipped": skipped,
        "errors": errors
    }


def get_latest_price(ticker: str) -> float:
    df = fetch_market_data(
        ticker=ticker,
        period="5d",
        interval="1d"
    )

    return round(float(df["Close"].iloc[-1]), 4)


def is_prediction_correct(
    predicted_direction: str,
    start_price: float,
    end_price: float
) -> bool:
    direction = predicted_direction.lower()

    if "bullish" in direction:
        return end_price > start_price

    if "bearish" in direction:
        return end_price < start_price

    return False
