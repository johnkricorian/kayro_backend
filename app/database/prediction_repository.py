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
    spy_entry_price: float,
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

        # Idempotence:
        # only one prediction per ticker/horizon/day.
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
            spy_entry_price=spy_entry_price,
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
    actual_direction: str,
    stock_return: float,
    spy_exit_price: float,
    spy_return: float,
    alpha: float,
    short_return: float | None,
    evaluation_market_date: datetime,
) -> bool:
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
            return False

        # Idempotence:
        # never evaluate the same prediction twice.
        if prediction.prediction_correct is not None:
            return False

        prediction.price_after_horizon = (
            price_after_horizon
        )

        prediction.prediction_correct = (
            prediction_correct
        )

        prediction.actual_direction = (
            actual_direction
        )

        prediction.stock_return = (
            stock_return
        )

        prediction.spy_exit_price = (
            spy_exit_price
        )

        prediction.spy_return = (
            spy_return
        )

        prediction.alpha = (
            alpha
        )

        prediction.short_return = (
            short_return
        )

        prediction.evaluation_market_date = (
            evaluation_market_date
        )

        prediction.evaluated_at = (
            datetime.utcnow()
        )

        db.commit()

        return True

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

def get_viability_stats() -> dict:
    db: Session = SessionLocal()

    try:
        predictions = (
            db.query(Prediction)
            .filter(
                Prediction.prediction_correct.is_not(None)
            )
            .all()
        )

        return _build_viability_stats(
            predictions
        )

    finally:
        db.close()

def _build_viability_stats(
    predictions: list[Prediction],
) -> dict:
    total = len(predictions)

    if total == 0:
        return {
            "evaluated_predictions": 0,
            "directional_predictions": 0,
            "direction_accuracy": 0.0,
            "balanced_accuracy": None,
            "bullish_precision": None,
            "bearish_precision": None,
            "class_support": {
                "actual_bullish": 0,
                "actual_bearish": 0,
            },
            "average_stock_return": 0.0,
            "average_spy_return": 0.0,
            "average_alpha": 0.0,
            "beat_spy_rate": 0.0,
            "relative_prediction_success_rate": 0.0,
            "average_short_return": 0.0,
            "confusion_matrix": (
                _empty_confusion_matrix()
            ),
            "by_horizon": [],
            "by_confidence": [],
        }

    directional = [
        prediction
        for prediction in predictions
        if (
            _normalize_direction(
                prediction.predicted_direction
            )
            in {"Bullish", "Bearish"}
            and _normalize_direction(
                prediction.actual_direction
            )
            in {"Bullish", "Bearish"}
        )
    ]

    direction_metrics = (
        _compute_direction_metrics(
            directional
        )
    )

    stock_returns = [
        prediction.stock_return
        for prediction in predictions
        if prediction.stock_return is not None
    ]

    spy_returns = [
        prediction.spy_return
        for prediction in predictions
        if prediction.spy_return is not None
    ]

    alphas = [
        prediction.alpha
        for prediction in predictions
        if prediction.alpha is not None
    ]

    short_returns = [
        prediction.short_return
        for prediction in predictions
        if prediction.short_return is not None
    ]

    beating_spy = [
        prediction
        for prediction in predictions
        if (
            prediction.alpha is not None
            and prediction.alpha > 0
        )
    ]

    relative_candidates = [
        prediction
        for prediction in predictions
        if (
            prediction.alpha is not None
            and _normalize_direction(
                prediction.predicted_direction
            )
            in {"Bullish", "Bearish"}
        )
    ]

    relative_success = [
        prediction
        for prediction in relative_candidates
        if _is_relative_prediction_success(
            prediction
        )
    ]

    horizons = sorted({
        prediction.forecast_horizon
        for prediction in predictions
    })

    confidence_buckets = [
        ("<50", 0, 50),
        ("50-59", 50, 60),
        ("60-69", 60, 70),
        ("70-79", 70, 80),
        ("80+", 80, None),
    ]

    return {
        "evaluated_predictions": total,

        "directional_predictions": len(
            directional
        ),

        "direction_accuracy": (
            direction_metrics[
                "direction_accuracy"
            ]
        ),

        "balanced_accuracy": (
            direction_metrics[
                "balanced_accuracy"
            ]
        ),

        "bullish_precision": (
            direction_metrics[
                "bullish_precision"
            ]
        ),

        "bearish_precision": (
            direction_metrics[
                "bearish_precision"
            ]
        ),

        "class_support": (
            direction_metrics[
                "class_support"
            ]
        ),

        "average_stock_return": (
            _percentage_average(
                stock_returns
            )
        ),

        "average_spy_return": (
            _percentage_average(
                spy_returns
            )
        ),

        "average_alpha": (
            _percentage_average(
                alphas
            )
        ),

        # Literal stock outperformance:
        # stock_return > SPY return.
        "beat_spy_rate": (
            _percentage_ratio(
                len(beating_spy),
                len(alphas),
            )
        ),

        # Direction-aware relative success:
        # Bullish -> alpha > 0
        # Bearish -> alpha < 0
        "relative_prediction_success_rate": (
            _percentage_ratio(
                len(relative_success),
                len(relative_candidates),
            )
        ),

        # Only bearish predictions have
        # a short_return.
        "average_short_return": (
            _percentage_average(
                short_returns
            )
        ),

        "confusion_matrix": (
            direction_metrics[
                "confusion_matrix"
            ]
        ),

        "by_horizon": [
            _build_viability_group(
                label=horizon,
                predictions=[
                    prediction
                    for prediction in predictions
                    if (
                        prediction.forecast_horizon
                        == horizon
                    )
                ],
            )
            for horizon in horizons
        ],

        "by_confidence": [
            _build_viability_group(
                label=label,
                predictions=[
                    prediction
                    for prediction in predictions
                    if _confidence_in_bucket(
                        prediction.direction_confidence,
                        minimum,
                        maximum,
                    )
                ],
            )
            for (
                label,
                minimum,
                maximum,
            )
            in confidence_buckets
        ],
    }


def _build_viability_group(
    label,
    predictions: list[Prediction],
) -> dict:
    directional = [
        prediction
        for prediction in predictions
        if (
            _normalize_direction(
                prediction.predicted_direction
            )
            in {"Bullish", "Bearish"}
            and _normalize_direction(
                prediction.actual_direction
            )
            in {"Bullish", "Bearish"}
        )
    ]

    metrics = (
        _compute_direction_metrics(
            directional
        )
    )

    stock_returns = [
        prediction.stock_return
        for prediction in predictions
        if prediction.stock_return is not None
    ]

    spy_returns = [
        prediction.spy_return
        for prediction in predictions
        if prediction.spy_return is not None
    ]

    alphas = [
        prediction.alpha
        for prediction in predictions
        if prediction.alpha is not None
    ]

    beating_spy = sum(
        1
        for alpha in alphas
        if alpha > 0
    )

    relative_candidates = [
        prediction
        for prediction in predictions
        if (
            prediction.alpha is not None
            and _normalize_direction(
                prediction.predicted_direction
            )
            in {"Bullish", "Bearish"}
        )
    ]

    relative_success = sum(
        1
        for prediction in relative_candidates
        if _is_relative_prediction_success(
            prediction
        )
    )

    short_returns = [
        prediction.short_return
        for prediction in predictions
        if prediction.short_return is not None
    ]

    return {
        "group": label,

        "evaluated_predictions": len(
            predictions
        ),

        "directional_predictions": len(
            directional
        ),

        "direction_accuracy": (
            metrics[
                "direction_accuracy"
            ]
        ),

        "balanced_accuracy": (
            metrics[
                "balanced_accuracy"
            ]
        ),

        "bullish_precision": (
            metrics[
                "bullish_precision"
            ]
        ),

        "bearish_precision": (
            metrics[
                "bearish_precision"
            ]
        ),

        "class_support": (
            metrics[
                "class_support"
            ]
        ),

        "average_stock_return": (
            _percentage_average(
                stock_returns
            )
        ),

        "average_spy_return": (
            _percentage_average(
                spy_returns
            )
        ),

        "average_alpha": (
            _percentage_average(
                alphas
            )
        ),

        "beat_spy_rate": (
            _percentage_ratio(
                beating_spy,
                len(alphas),
            )
        ),

        "relative_prediction_success_rate": (
            _percentage_ratio(
                relative_success,
                len(relative_candidates),
            )
        ),

        "average_short_return": (
            _percentage_average(
                short_returns
            )
        ),
    }

def _compute_direction_metrics(
    predictions: list[Prediction],
) -> dict:
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for prediction in predictions:
        predicted = _normalize_direction(
            prediction.predicted_direction
        )

        actual = _normalize_direction(
            prediction.actual_direction
        )

        if (
            predicted == "Bullish"
            and actual == "Bullish"
        ):
            tp += 1

        elif (
            predicted == "Bearish"
            and actual == "Bearish"
        ):
            tn += 1

        elif (
            predicted == "Bullish"
            and actual == "Bearish"
        ):
            fp += 1

        elif (
            predicted == "Bearish"
            and actual == "Bullish"
        ):
            fn += 1

    total = (
        tp
        + tn
        + fp
        + fn
    )

    bullish_support = (
        tp + fn
    )

    bearish_support = (
        tn + fp
    )

    direction_accuracy = (
        _percentage_ratio(
            tp + tn,
            total,
        )
    )

    bullish_recall = (
        _ratio(
            tp,
            bullish_support,
        )
        if bullish_support > 0
        else None
    )

    bearish_recall = (
        _ratio(
            tn,
            bearish_support,
        )
        if bearish_support > 0
        else None
    )

    if (
        bullish_recall is not None
        and bearish_recall is not None
    ):
        balanced_accuracy = round(
            (
                bullish_recall
                + bearish_recall
            )
            / 2
            * 100,
            2,
        )
    else:
        balanced_accuracy = None

    bullish_precision = (
        _percentage_ratio(
            tp,
            tp + fp,
        )
        if (tp + fp) > 0
        else None
    )

    bearish_precision = (
        _percentage_ratio(
            tn,
            tn + fn,
        )
        if (tn + fn) > 0
        else None
    )

    return {
        "direction_accuracy": (
            direction_accuracy
        ),
        "balanced_accuracy": (
            balanced_accuracy
        ),
        "bullish_precision": (
            bullish_precision
        ),
        "bearish_precision": (
            bearish_precision
        ),
        "class_support": {
            "actual_bullish": bullish_support,
            "actual_bearish": bearish_support,
        },
        "confusion_matrix": {
            "actual_bullish": {
                "predicted_bullish": tp,
                "predicted_bearish": fn,
            },
            "actual_bearish": {
                "predicted_bullish": fp,
                "predicted_bearish": tn,
            },
        },
    }

def _normalize_direction(
    direction: str | None,
) -> str:
    if not direction:
        return "Neutral"

    normalized = direction.lower()

    if "bullish" in normalized:
        return "Bullish"

    if "bearish" in normalized:
        return "Bearish"

    return "Neutral"


def _is_relative_prediction_success(
    prediction: Prediction,
) -> bool:
    if prediction.alpha is None:
        return False

    direction = _normalize_direction(
        prediction.predicted_direction
    )

    if direction == "Bullish":
        return prediction.alpha > 0

    if direction == "Bearish":
        return prediction.alpha < 0

    return False


def _confidence_in_bucket(
    confidence: float | None,
    minimum: float,
    maximum: float | None,
) -> bool:
    if confidence is None:
        return False

    if confidence < minimum:
        return False

    if (
        maximum is not None
        and confidence >= maximum
    ):
        return False

    return True


def _ratio(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def _percentage_ratio(
    numerator: int,
    denominator: int,
) -> float:
    return round(
        _ratio(
            numerator,
            denominator,
        )
        * 100,
        2,
    )


def _percentage_average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return round(
        (
            sum(values)
            / len(values)
        )
        * 100,
        2,
    )


def _empty_confusion_matrix() -> dict:
    return {
        "actual_bullish": {
            "predicted_bullish": 0,
            "predicted_bearish": 0,
        },
        "actual_bearish": {
            "predicted_bullish": 0,
            "predicted_bearish": 0,
        },
    }
