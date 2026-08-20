from datetime import datetime

import pandas as pd

from app.database.prediction_repository import (
    get_pending_predictions,
    update_prediction_result,
)
from app.services.market import fetch_market_data


NEUTRAL_THRESHOLD = 0.02


def evaluate_pending_predictions() -> dict:
    predictions = get_pending_predictions()

    evaluated = 0
    skipped = 0
    errors = []

    for prediction in predictions:
        try:
            price_after_horizon = get_price_after_sessions(
                ticker=prediction.ticker,
                created_at=prediction.created_at,
                forecast_horizon=prediction.forecast_horizon,
            )

            # Not enough trading sessions have elapsed yet.
            if price_after_horizon is None:
                skipped += 1
                continue

            prediction_correct = is_prediction_correct(
                predicted_direction=prediction.predicted_direction,
                start_price=prediction.price_at_prediction,
                end_price=price_after_horizon,
            )

            update_prediction_result(
                prediction_id=prediction.id,
                price_after_horizon=price_after_horizon,
                prediction_correct=prediction_correct,
            )

            evaluated += 1

        except Exception as error:
            errors.append({
                "prediction_id": prediction.id,
                "ticker": prediction.ticker,
                "error": str(error),
            })

    return {
        "pending": len(predictions),
        "evaluated": evaluated,
        "skipped": skipped,
        "errors": errors,
    }


def get_price_after_sessions(
    ticker: str,
    created_at: datetime,
    forecast_horizon: int,
) -> float | None:
    if forecast_horizon <= 0:
        return None

    df = fetch_market_data(
        ticker=ticker,
        period="6mo",
        interval="1d",
    )

    if df is None or df.empty:
        return None

    df = df.copy()

    # Handle both:
    # - Date stored in the index
    # - Date stored as a dataframe column
    if "Date" not in df.columns:
        df = df.reset_index()

    if "Date" not in df.columns:
        return None

    df["Date"] = pd.to_datetime(
        df["Date"],
        utc=True,
    ).dt.tz_localize(None)

    prediction_date = pd.Timestamp(
        created_at
    ).tz_localize(None).normalize()

    # Prediction uses the latest known market price.
    # Horizon 1 therefore means the NEXT trading session.
    future_sessions = (
        df[
            df["Date"].dt.normalize()
            > prediction_date
        ]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    if len(future_sessions) < forecast_horizon:
        return None

    target_row = future_sessions.iloc[
        forecast_horizon - 1
    ]

    return round(
        float(target_row["Close"]),
        4
    )


def is_prediction_correct(
    predicted_direction: str,
    start_price: float | None,
    end_price: float,
) -> bool:
    if start_price is None or start_price <= 0:
        return False

    direction = predicted_direction.lower()

    if "bullish" in direction:
        return end_price > start_price

    if "bearish" in direction:
        return end_price < start_price

    if "neutral" in direction:
        price_change = (
            end_price / start_price
        ) - 1.0

        return abs(price_change) <= NEUTRAL_THRESHOLD

    return False
