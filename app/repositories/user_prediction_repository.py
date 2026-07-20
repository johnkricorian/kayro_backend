from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import UserPrediction


def save_user_prediction(
    db: Session,
    *,
    user_id: str,
    ticker: str,
    forecast_horizon: int,
    prediction_payload: dict,
) -> UserPrediction:
    normalized_ticker = ticker.strip().upper()

    row = (
        db.query(UserPrediction)
        .filter(
            UserPrediction.user_id == user_id,
            UserPrediction.ticker == normalized_ticker,
            UserPrediction.forecast_horizon == forecast_horizon,
        )
        .one_or_none()
    )

    prediction = prediction_payload.get("prediction", {})
    market_context = prediction_payload.get("market_context", {})

    if row is None:
        row = UserPrediction(
            user_id=user_id,
            ticker=normalized_ticker,
            forecast_horizon=forecast_horizon,
        )

        db.add(row)

    row.status = "ready"
    row.kayro_score = prediction_payload.get("kayro_score")
    row.recommendation = prediction_payload.get("recommendation")
    row.confidence = prediction_payload.get("confidence")

    row.direction = prediction.get("direction")
    row.probability_up = prediction.get("probability_up")
    row.probability_down = prediction.get("probability_down")
    row.target_price = prediction.get("target")

    row.latest_close = market_context.get("latest_close")
    row.prediction_payload = prediction_payload
    row.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(row)
        return row

    except Exception:
        db.rollback()
        raise


def get_user_predictions(
    db: Session,
    *,
    user_id: str,
) -> list[UserPrediction]:
    return (
        db.query(UserPrediction)
        .filter(
            UserPrediction.user_id == user_id
        )
        .order_by(
            UserPrediction.created_at.desc()
        )
        .all()
    )


def get_user_prediction(
    db: Session,
    *,
    user_id: str,
    ticker: str,
    forecast_horizon: int,
) -> UserPrediction | None:
    return (
        db.query(UserPrediction)
        .filter(
            UserPrediction.user_id == user_id,
            UserPrediction.ticker == ticker.strip().upper(),
            UserPrediction.forecast_horizon == forecast_horizon,
        )
        .one_or_none()
    )


def delete_user_prediction(
    db: Session,
    *,
    user_id: str,
    ticker: str,
    forecast_horizon: int,
) -> bool:
    row = get_user_prediction(
        db,
        user_id=user_id,
        ticker=ticker,
        forecast_horizon=forecast_horizon,
    )

    if row is None:
        return False

    try:
        db.delete(row)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
