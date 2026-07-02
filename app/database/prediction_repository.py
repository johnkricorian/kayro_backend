from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import SessionLocal
from app.database.models import Prediction

def save_prediction(
    ticker: str,
    forecast_horizon: int,
    predicted_direction: str,
    probability_up: float,
    confidence: float,
    kayro_score: int,
    recommendation: str,
    price_at_prediction: float,
):

    db: Session = SessionLocal()

    try:

        prediction = Prediction(
            ticker=ticker,
            forecast_horizon=forecast_horizon,
            predicted_direction=predicted_direction,
            probability_up=probability_up,
            confidence=confidence,
            kayro_score=kayro_score,
            recommendation=recommendation,
            price_at_prediction=price_at_prediction,
        )

        db.add(prediction)
        db.commit()

    finally:
        db.close()

from sqlalchemy import desc

def get_predictions(limit: int = 100):

    db = SessionLocal()

    try:
        return (
            db.query(Prediction)
            .order_by(desc(Prediction.created_at))
            .limit(limit)
            .all()
        )

    finally:
        db.close()
