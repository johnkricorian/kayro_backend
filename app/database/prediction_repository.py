from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import SessionLocal
from app.database.models import Prediction
from datetime import datetime, timedelta
from sqlalchemy import func

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

def get_pending_predictions():
    db = SessionLocal()

    try:
        return (
            db.query(Prediction)
            .filter(Prediction.prediction_correct.is_(None))
            .all()
        )

    finally:
        db.close()


def update_prediction_result(
    prediction_id: int,
    price_after_horizon: float,
    prediction_correct: bool
):
    db = SessionLocal()

    try:
        prediction = (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id)
            .first()
        )

        if prediction is None:
            return

        prediction.price_after_horizon = price_after_horizon
        prediction.prediction_correct = prediction_correct
        prediction.evaluated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()

        from datetime import datetime

from app.database.database import SessionLocal
from app.database.models import Prediction


def get_pending_predictions():
    db = SessionLocal()

    try:
        return (
            db.query(Prediction)
            .filter(Prediction.prediction_correct.is_(None))
            .all()
        )

    finally:
        db.close()


def update_prediction_result(
    prediction_id: int,
    price_after_horizon: float,
    prediction_correct: bool
):
    db = SessionLocal()

    try:
        prediction = (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id)
            .first()
        )

        if prediction is None:
            return

        prediction.price_after_horizon = price_after_horizon
        prediction.prediction_correct = prediction_correct
        prediction.evaluated_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()

def get_global_stats() -> dict:
    db = SessionLocal()

    try:
        total = db.query(Prediction).count()

        evaluated = (
            db.query(Prediction)
            .filter(Prediction.prediction_correct.is_not(None))
            .count()
        )

        correct = (
            db.query(Prediction)
            .filter(Prediction.prediction_correct.is_(True))
            .count()
        )

        avg_confidence = (
            db.query(func.avg(Prediction.confidence))
            .scalar()
        ) or 0

        avg_score = (
            db.query(func.avg(Prediction.kayro_score))
            .scalar()
        ) or 0

        bullish = (
            db.query(Prediction)
            .filter(Prediction.predicted_direction.ilike("%bullish%"))
            .count()
        )

        bearish = (
            db.query(Prediction)
            .filter(Prediction.predicted_direction.ilike("%bearish%"))
            .count()
        )

        accuracy = (
            round((correct / evaluated) * 100, 2)
            if evaluated > 0
            else 0
        )

        return {
            "total_predictions": total,
            "evaluated_predictions": evaluated,
            "pending_predictions": total - evaluated,
            "correct_predictions": correct,
            "accuracy": accuracy,
            "average_confidence": round(float(avg_confidence), 2),
            "average_kayro_score": round(float(avg_score), 2),
            "bullish_predictions": bullish,
            "bearish_predictions": bearish
        }

    finally:
        db.close()
