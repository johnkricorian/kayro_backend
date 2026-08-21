from datetime import datetime, timedelta
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import Prediction

def save_prediction(
    ticker: str,
    forecast_horizon: int,
    predicted_direction: str,
    probability_up: float,
    direction_confidence: float,
    qeyro_score: int,
    recommendation: str,
    target_price: float,
    price_at_prediction: float,
    technical_score: float,
    news_score: float,
    market_score: float,
) -> None:
    db: Session = SessionLocal()

    try:
        now = datetime.utcnow()

        start_of_day = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
        )

        end_of_day = (
            start_of_day
            + timedelta(days=1)
        )

        existing = (
            db.query(Prediction)
            .filter(
                Prediction.ticker == ticker.upper(),
                Prediction.forecast_horizon == forecast_horizon,
                Prediction.created_at >= start_of_day,
                Prediction.created_at < end_of_day,
            )
            .first()
        )

        if existing is not None:
            return

        prediction = Prediction(
            ticker=ticker.upper(),
            forecast_horizon=forecast_horizon,
            predicted_direction=predicted_direction,
            probability_up=probability_up,
            direction_confidence=direction_confidence,
            qeyro_score=qeyro_score,
            recommendation=recommendation,
            target_price=target_price,
            price_at_prediction=price_at_prediction,
            technical_score=technical_score,
            news_score=news_score,
            market_score=market_score,
        )

        db.add(prediction)
        db.commit()

    finally:
        db.close()


def get_predictions(
    limit: int = 100
) -> list[Prediction]:
    db: Session = SessionLocal()

    try:
        return (
            db.query(Prediction)
            .order_by(
                desc(Prediction.created_at)
            )
            .limit(limit)
            .all()
        )

    finally:
        db.close()


def get_pending_predictions() -> list[Prediction]:
    db: Session = SessionLocal()

    try:
        return (
            db.query(Prediction)
            .filter(
                Prediction.prediction_correct.is_(None)
            )
            .all()
        )

    finally:
        db.close()


def update_prediction_result(
    prediction_id: int,
    price_after_horizon: float,
    prediction_correct: bool,
) -> None:
    db: Session = SessionLocal()

    try:
        prediction = (
            db.query(Prediction)
            .filter(
                Prediction.id == prediction_id
            )
            .first()
        )

        if prediction is None:
            return

        prediction.price_after_horizon = (
            price_after_horizon
        )

        prediction.prediction_correct = (
            prediction_correct
        )

        prediction.evaluated_at = (
            datetime.utcnow()
        )

        db.commit()

    finally:
        db.close()


def get_global_stats() -> dict:
    db: Session = SessionLocal()

    try:
        total = (
            db.query(Prediction)
            .count()
        )

        evaluated = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .count()
        )

        correct = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_correct.is_(True)
            )
            .count()
        )

        avg_confidence = (
            db.query(
                func.avg(
                    Prediction.direction_confidence
                )
            )
            .scalar()
        ) or 0

        avg_score = (
            db.query(
                func.avg(
                    Prediction.qeyro_score
                )
            )
            .scalar()
        ) or 0

        bullish = (
            db.query(Prediction)
            .filter(
                Prediction.predicted_direction.ilike(
                    "%bullish%"
                )
            )
            .count()
        )

        bearish = (
            db.query(Prediction)
            .filter(
                Prediction.predicted_direction.ilike(
                    "%bearish%"
                )
            )
            .count()
        )

        accuracy = (
            round(
                correct / evaluated * 100,
                2
            )
            if evaluated > 0
            else 0.0
        )

        return {
            "total_predictions": total,
            "evaluated_predictions": evaluated,
            "pending_predictions": (
                total - evaluated
            ),
            "correct_predictions": correct,
            "accuracy": accuracy,
            "average_direction_confidence": round(
                float(avg_confidence),
                2
            ),
            "average_qeyro_score": round(
                float(avg_score),
                2
            ),
            "bullish_predictions": bullish,
            "bearish_predictions": bearish,
        }

    finally:
        db.close()


def get_ticker_stats(
    ticker: str
) -> dict:
    ticker = ticker.upper()

    db: Session = SessionLocal()

    try:
        query = (
            db.query(Prediction)
            .filter(
                Prediction.ticker == ticker
            )
        )

        total = query.count()

        evaluated = (
            query
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .count()
        )

        correct = (
            query
            .filter(
                Prediction.prediction_correct.is_(True)
            )
            .count()
        )

        avg_confidence = (
            query
            .with_entities(
                func.avg(
                    Prediction.direction_confidence
                )
            )
            .scalar()
        ) or 0

        avg_score = (
            query
            .with_entities(
                func.avg(
                    Prediction.qeyro_score
                )
            )
            .scalar()
        ) or 0

        accuracy = (
            round(
                correct / evaluated * 100,
                2
            )
            if evaluated > 0
            else 0.0
        )

        return {
            "ticker": ticker,
            "total_predictions": total,
            "evaluated_predictions": evaluated,
            "pending_predictions": (
                total - evaluated
            ),
            "correct_predictions": correct,
            "accuracy": accuracy,
            "average_direction_confidence": round(
                float(avg_confidence),
                2
            ),
            "average_qeyro_score": round(
                float(avg_score),
                2
            ),
        }

    finally:
        db.close()


def get_horizon_stats() -> list[dict]:
    db: Session = SessionLocal()

    try:
        rows = (
            db.query(
                Prediction.forecast_horizon,
                func.count(
                    Prediction.id
                ).label("evaluated"),
                func.sum(
                    case(
                        (
                            Prediction.prediction_correct.is_(True),
                            1
                        ),
                        else_=0
                    )
                ).label("correct"),
                func.avg(
                    Prediction.qeyro_score
                ).label("avg_qeyro_score"),
                func.avg(
                    Prediction.direction_confidence
                ).label("avg_confidence"),
            )
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .group_by(
                Prediction.forecast_horizon
            )
            .order_by(
                Prediction.forecast_horizon
            )
            .all()
        )

        stats = []

        for row in rows:
            evaluated = int(
                row.evaluated or 0
            )

            correct = int(
                row.correct or 0
            )

            accuracy = (
                round(
                    correct / evaluated * 100,
                    2
                )
                if evaluated > 0
                else 0.0
            )

            stats.append({
                "forecast_horizon": (
                    row.forecast_horizon
                ),
                "evaluated_predictions": (
                    evaluated
                ),
                "correct_predictions": (
                    correct
                ),
                "accuracy": accuracy,
                "average_qeyro_score": round(
                    float(
                        row.avg_qeyro_score or 0
                    ),
                    2
                ),
                "average_direction_confidence": round(
                    float(
                        row.avg_confidence or 0
                    ),
                    2
                ),
            })

        return stats

    finally:
        db.close()


def get_leaderboard(
    limit: int = 20
) -> list[dict]:
    db: Session = SessionLocal()

    try:
        rows = (
            db.query(
                Prediction.ticker,
                func.count(
                    Prediction.id
                ).label("total"),
                func.sum(
                    case(
                        (
                            Prediction.prediction_correct.is_(True),
                            1
                        ),
                        else_=0
                    )
                ).label("correct"),
                func.avg(
                    Prediction.direction_confidence
                ).label("avg_confidence"),
                func.avg(
                    Prediction.qeyro_score
                ).label("avg_score"),
            )
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .group_by(
                Prediction.ticker
            )
            .all()
        )

        leaderboard = []

        for row in rows:
            total = int(
                row.total or 0
            )

            correct = int(
                row.correct or 0
            )

            accuracy = (
                round(
                    correct / total * 100,
                    2
                )
                if total > 0
                else 0.0
            )

            leaderboard.append({
                "ticker": row.ticker,
                "predictions": total,
                "correct_predictions": correct,
                "accuracy": accuracy,
                "average_direction_confidence": round(
                    float(
                        row.avg_confidence or 0
                    ),
                    2
                ),
                "average_qeyro_score": round(
                    float(
                        row.avg_score or 0
                    ),
                    2
                ),
            })

        return sorted(
            leaderboard,
            key=lambda item: (
                item["accuracy"]
            ),
            reverse=True,
        )[:limit]

    finally:
        db.close()

def get_score_bucket_stats() -> list[dict]:
    db: Session = SessionLocal()

    try:
        evaluated_predictions = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .all()
        )

        buckets = [
            {
                "label": "<50",
                "min": None,
                "max": 49,
            },
            {
                "label": "50-59",
                "min": 50,
                "max": 59,
            },
            {
                "label": "60-69",
                "min": 60,
                "max": 69,
            },
            {
                "label": "70-79",
                "min": 70,
                "max": 79,
            },
            {
                "label": "80+",
                "min": 80,
                "max": None,
            },
        ]

        stats = []

        for bucket in buckets:
            predictions = [
                prediction
                for prediction in evaluated_predictions
                if _score_in_bucket(
                    score=prediction.qeyro_score,
                    minimum=bucket["min"],
                    maximum=bucket["max"],
                )
            ]

            total = len(
                predictions
            )

            correct = sum(
                1
                for prediction in predictions
                if prediction.prediction_correct is True
            )

            accuracy = (
                round(
                    correct / total * 100,
                    2
                )
                if total > 0
                else 0.0
            )

            avg_confidence = (
                sum(
                    prediction.direction_confidence
                    for prediction in predictions
                )
                / total
                if total > 0
                else 0.0
            )

            avg_score = (
                sum(
                    prediction.qeyro_score
                    for prediction in predictions
                )
                / total
                if total > 0
                else 0.0
            )

            stats.append({
                "bucket": bucket["label"],
                "evaluated_predictions": total,
                "correct_predictions": correct,
                "accuracy": accuracy,
                "average_qeyro_score": round(
                    avg_score,
                    2
                ),
                "average_direction_confidence": round(
                    avg_confidence,
                    2
                ),
            })

        return stats

    finally:
        db.close()


def _score_in_bucket(
    score: int,
    minimum: int | None,
    maximum: int | None,
) -> bool:
    if minimum is not None and score < minimum:
        return False

    if maximum is not None and score > maximum:
        return False

    return True

def get_today_prediction(
    ticker: str,
    forecast_horizon: int,
) -> Prediction | None:
    db: Session = SessionLocal()

    try:
        today = datetime.utcnow().date()

        return (
            db.query(Prediction)
            .filter(
                Prediction.ticker == ticker.upper(),
                Prediction.forecast_horizon == forecast_horizon,
                func.date(Prediction.created_at) == today.isoformat(),
            )
            .order_by(
                Prediction.created_at.desc()
            )
            .first()
        )

    finally:
        db.close()
