import math

from datetime import datetime, timedelta

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models import Prediction

PORTFOLIO_INITIAL_CAPITAL = 10_000.0
PORTFOLIO_POSITION_SIZE = 1_000.0
PORTFOLIO_MAX_OPEN_POSITIONS = 10
PROSPECTIVE_VALIDATION_START = datetime(2026, 8, 31,)

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
    limit: int = 100,
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
    strategy_return: float,
    strategy_alpha: float,
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

        prediction.strategy_return = (
            strategy_return
        )

        prediction.strategy_alpha = (
            strategy_alpha
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
                2,
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
                2,
            ),
            "average_qeyro_score": round(
                float(avg_score),
                2,
            ),
            "bullish_predictions": bullish,
            "bearish_predictions": bearish,
        }

    finally:
        db.close()


def get_ticker_stats(
    ticker: str,
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
                2,
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
                2,
            ),
            "average_qeyro_score": round(
                float(avg_score),
                2,
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
                            1,
                        ),
                        else_=0,
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
                    2,
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
                    2,
                ),
                "average_direction_confidence": round(
                    float(
                        row.avg_confidence or 0
                    ),
                    2,
                ),
            })

        return stats

    finally:
        db.close()


def get_leaderboard(
    limit: int = 20,
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
                            1,
                        ),
                        else_=0,
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
                    2,
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
                    2,
                ),
                "average_qeyro_score": round(
                    float(
                        row.avg_score or 0
                    ),
                    2,
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
                    2,
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
                    2,
                ),
                "average_direction_confidence": round(
                    avg_confidence,
                    2,
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
        today = (
            datetime.utcnow()
            .date()
        )

        return (
            db.query(Prediction)
            .filter(
                Prediction.ticker == ticker.upper(),
                Prediction.forecast_horizon == forecast_horizon,
                func.date(
                    Prediction.created_at
                ) == today.isoformat(),
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
            .order_by(
                Prediction.created_at.asc(),
                Prediction.id.asc(),
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
            "sample_size": 0,
            "sample_maturity": "insufficient",
            "direction_accuracy": 0.0,
            "confidence_interval_95": None,
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
            "average_strategy_return": 0.0,
            "average_strategy_alpha": 0.0,
            "cumulative_strategy_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": None,
            "prospective_validation": {
                "start_date": (
                    PROSPECTIVE_VALIDATION_START
                    .date()
                    .isoformat()
                ),
                "evaluated_predictions": 0,
                "directional_predictions": 0,
                "sample_maturity": "insufficient",
                "direction_accuracy": 0.0,
                "confidence_interval_95": None,
                "progress": {
                    "target_30": 0.0,
                    "target_100": 0.0,
                    "target_300": 0.0,
                },
                "portfolio": (
                    build_theoretical_portfolio([])
                ),
            },
            "theoretical_portfolio": (
                build_theoretical_portfolio([])
            ),

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

    strategy_returns = [
        strategy_return
        for prediction in predictions
        if (
            strategy_return := getattr(
                prediction,
                "strategy_return",
                None,
            )
        ) is not None
    ]

    strategy_alphas = [
        strategy_alpha
        for prediction in predictions
        if (
            strategy_alpha := getattr(
                prediction,
                "strategy_alpha",
                None,
            )
        ) is not None
    ]

    cumulative_strategy_return = (
        calculate_cumulative_return(
            strategy_returns
        )
    )

    max_drawdown = (
        calculate_max_drawdown(
            strategy_returns
        )
    )

    sharpe_ratio = (
        calculate_sharpe_ratio(
            strategy_returns
        )
    )

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

    prospective_predictions = [
        prediction
        for prediction in predictions
        if (
            (
                created_at := getattr(
                    prediction,
                    "created_at",
                    None,
                )
            )
            is not None
            and created_at
            >= PROSPECTIVE_VALIDATION_START
        )
    ]

    prospective_directional = [
        prediction
        for prediction in prospective_predictions
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

    prospective_metrics = (
        _compute_direction_metrics(
            prospective_directional
        )
    )

    prospective_portfolio = (
        build_theoretical_portfolio(
            prospective_predictions
        )
    )

    prospective_sample_size = len(
        prospective_directional
    )

    theoretical_portfolio = (
        build_theoretical_portfolio(
            predictions
        )
    )

    return {
        "evaluated_predictions": total,

        "directional_predictions": len(
            directional
        ),

        "sample_size": (
            direction_metrics[
                "sample_size"
            ]
        ),

        "sample_maturity": (
            direction_metrics[
                "sample_maturity"
            ]
        ),

        "direction_accuracy": (
            direction_metrics[
                "direction_accuracy"
            ]
        ),

        "confidence_interval_95": (
            direction_metrics[
                "confidence_interval_95"
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

        "beat_spy_rate": (
            _percentage_ratio(
                len(beating_spy),
                len(alphas),
            )
        ),

        "relative_prediction_success_rate": (
            _percentage_ratio(
                len(relative_success),
                len(relative_candidates),
            )
        ),

        "average_short_return": (
            _percentage_average(
                short_returns
            )
        ),

        "average_strategy_return": (
            _percentage_average(
                strategy_returns
            )
        ),

        "average_strategy_alpha": (
            _percentage_average(
                strategy_alphas
            )
        ),

        "cumulative_strategy_return": (
            cumulative_strategy_return
        ),

        "max_drawdown": (
            max_drawdown
        ),

        "sharpe_ratio": (
            sharpe_ratio
        ),


        "prospective_validation": {
            "start_date": (
                PROSPECTIVE_VALIDATION_START
                .date()
                .isoformat()
            ),

            "evaluated_predictions": len(
                prospective_predictions
            ),

            "directional_predictions": (
                prospective_sample_size
            ),

            "sample_maturity": (
                prospective_metrics[
                    "sample_maturity"
                ]
            ),

            "direction_accuracy": (
                prospective_metrics[
                    "direction_accuracy"
                ]
            ),

            "confidence_interval_95": (
                prospective_metrics[
                    "confidence_interval_95"
                ]
            ),

            "progress": {
                "target_30": round(
                    min(
                        prospective_sample_size / 30 * 100,
                        100,
                    ),
                    2,
                ),
                "target_100": round(
                    min(
                        prospective_sample_size / 100 * 100,
                        100,
                    ),
                    2,
                ),
                "target_300": round(
                    min(
                        prospective_sample_size / 300 * 100,
                        100,
                    ),
                    2,
                ),
            },

            "portfolio": (
                prospective_portfolio
            ),
        },

        "theoretical_portfolio": (
            theoretical_portfolio
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
            ) in confidence_buckets
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

    short_returns = [
        prediction.short_return
        for prediction in predictions
        if prediction.short_return is not None
    ]

    strategy_returns = [
        strategy_return
        for prediction in predictions
        if (
            strategy_return := getattr(
                prediction,
                "strategy_return",
                None,
            )
        ) is not None
    ]

    strategy_alphas = [
        strategy_alpha
        for prediction in predictions
        if (
            strategy_alpha := getattr(
                prediction,
                "strategy_alpha",
                None,
            )
        ) is not None
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

    return {
        "group": label,

        "evaluated_predictions": len(
            predictions
        ),

        "directional_predictions": len(
            directional
        ),

        "sample_size": (
            metrics[
                "sample_size"
            ]
        ),

        "sample_maturity": (
            metrics[
                "sample_maturity"
            ]
        ),

        "direction_accuracy": (
            metrics[
                "direction_accuracy"
            ]
        ),

        "confidence_interval_95": (
            metrics[
                "confidence_interval_95"
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

        "average_strategy_return": (
            _percentage_average(
                strategy_returns
            )
        ),

        "average_strategy_alpha": (
            _percentage_average(
                strategy_alphas
            )
        ),

        "cumulative_strategy_return": (
            calculate_cumulative_return(
                strategy_returns
            )
        ),

        "max_drawdown": (
            calculate_max_drawdown(
                strategy_returns
            )
        ),

        "sharpe_ratio": (
            calculate_sharpe_ratio(
                strategy_returns
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

    confidence_interval_95 = (
        calculate_wilson_confidence_interval(
            successes=tp + tn,
            sample_size=total,
        )
    )

    sample_maturity = (
        get_sample_maturity(
            sample_size=total,
        )
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
        "sample_size": total,

        "sample_maturity": (
            sample_maturity
        ),

        "direction_accuracy": (
            direction_accuracy
        ),

        "confidence_interval_95": (
            confidence_interval_95
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

    normalized = (
        direction.lower()
    )

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
        return (
            prediction.alpha > 0
        )

    if direction == "Bearish":
        return (
            prediction.alpha < 0
        )

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

    return (
        numerator
        / denominator
    )


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


def calculate_wilson_confidence_interval(
    successes: int,
    sample_size: int,
    z: float = 1.96,
) -> dict | None:
    if sample_size == 0:
        return None

    proportion = (
        successes
        / sample_size
    )

    z_squared = (
        z ** 2
    )

    denominator = (
        1
        + z_squared / sample_size
    )

    center = (
        proportion
        + z_squared
        / (2 * sample_size)
    ) / denominator

    margin = (
        z
        * math.sqrt(
            (
                proportion
                * (1 - proportion)
                + z_squared
                / (4 * sample_size)
            )
            / sample_size
        )
        / denominator
    )

    return {
        "lower": round(
            max(
                0.0,
                center - margin,
            )
            * 100,
            2,
        ),
        "upper": round(
            min(
                1.0,
                center + margin,
            )
            * 100,
            2,
        ),
    }


def get_sample_maturity(
    sample_size: int,
) -> str:
    if sample_size < 30:
        return "insufficient"

    if sample_size < 100:
        return "early"

    if sample_size < 300:
        return "indicative"

    return "reliable"

def calculate_cumulative_return(
    returns: list[float],
) -> float:
    if not returns:
        return 0.0

    portfolio_value = 1.0

    for strategy_return in returns:
        portfolio_value *= (
            1.0 + strategy_return
        )

    return round(
        (portfolio_value - 1.0) * 100,
        2,
    )


def calculate_max_drawdown(
    returns: list[float],
) -> float:
    if not returns:
        return 0.0

    portfolio_value = 1.0
    peak_value = 1.0
    max_drawdown = 0.0

    for strategy_return in returns:
        portfolio_value *= (
            1.0 + strategy_return
        )

        peak_value = max(
            peak_value,
            portfolio_value,
        )

        drawdown = (
            portfolio_value
            / peak_value
            - 1.0
        )

        max_drawdown = min(
            max_drawdown,
            drawdown,
        )

    return round(
        max_drawdown * 100,
        2,
    )


def calculate_sharpe_ratio(
    returns: list[float],
) -> float | None:
    if len(returns) < 2:
        return None

    mean_return = (
        sum(returns)
        / len(returns)
    )

    variance = (
        sum(
            (
                strategy_return
                - mean_return
            ) ** 2
            for strategy_return in returns
        )
        / (len(returns) - 1)
    )

    standard_deviation = math.sqrt(
        variance
    )

    if math.isclose(
        standard_deviation,
        0.0,
        abs_tol=1e-12,
    ):
        return None

    return round(
        mean_return
        / standard_deviation,
        4,
    )

def calculate_position_pnl(
    predicted_direction: str,
    stock_return: float,
    position_size: float = PORTFOLIO_POSITION_SIZE,
) -> float:
    direction = _normalize_direction(
        predicted_direction
    )

    if direction == "Bullish":
        return round(
            position_size * stock_return,
            2,
        )

    if direction == "Bearish":
        return round(
            position_size * -stock_return,
            2,
        )

    return 0.0


def calculate_spy_benchmark(
    predictions: list[Prediction],
    initial_capital: float = PORTFOLIO_INITIAL_CAPITAL,
) -> dict:
    eligible_predictions = [
        prediction
        for prediction in predictions
        if (
            getattr(
                prediction,
                "created_at",
                None,
            ) is not None
            and getattr(
                prediction,
                "evaluation_market_date",
                None,
            ) is not None
            and getattr(
                prediction,
                "spy_entry_price",
                None,
            ) is not None
            and getattr(
                prediction,
                "spy_exit_price",
                None,
            ) is not None
        )
    ]

    if not eligible_predictions:
        return {
            "spy_start_price": None,
            "spy_end_price": None,
            "spy_return": 0.0,
            "spy_final_equity": round(
                initial_capital,
                2,
            ),
        }

    first_prediction = min(
        eligible_predictions,
        key=lambda prediction: (
            _as_date(
                getattr(
                    prediction,
                    "created_at",
                )
            ),
            getattr(
                prediction,
                "id",
                0,
            ) or 0,
        ),
    )

    last_prediction = max(
        eligible_predictions,
        key=lambda prediction: (
            _as_date(
                getattr(
                    prediction,
                    "evaluation_market_date",
                )
            ),
            getattr(
                prediction,
                "id",
                0,
            ) or 0,
        ),
    )

    spy_start_price = float(
        first_prediction.spy_entry_price
    )

    spy_end_price = float(
        last_prediction.spy_exit_price
    )

    if spy_start_price <= 0:
        return {
            "spy_start_price": None,
            "spy_end_price": None,
            "spy_return": 0.0,
            "spy_final_equity": round(
                initial_capital,
                2,
            ),
        }

    spy_return = (
        spy_end_price
        / spy_start_price
        - 1.0
    )

    spy_final_equity = (
        initial_capital
        * (1.0 + spy_return)
    )

    return {
        "spy_start_price": round(
            spy_start_price,
            2,
        ),
        "spy_end_price": round(
            spy_end_price,
            2,
        ),
        "spy_return": round(
            spy_return * 100,
            2,
        ),
        "spy_final_equity": round(
            spy_final_equity,
            2,
        ),
    }


def build_theoretical_portfolio(
    predictions: list[Prediction],
    initial_capital: float = PORTFOLIO_INITIAL_CAPITAL,
    position_size: float = PORTFOLIO_POSITION_SIZE,
    max_open_positions: int = PORTFOLIO_MAX_OPEN_POSITIONS,
) -> dict:
    if not predictions:
        return {
            "initial_capital": initial_capital,
            "final_equity": initial_capital,
            "realized_pnl": 0.0,
            "total_return": 0.0,
            "positions_taken": 0,
            "positions_skipped": 0,
            "winning_positions": 0,
            "losing_positions": 0,
            "flat_positions": 0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "benchmark": {
                "spy_start_price": None,
                "spy_end_price": None,
                "spy_return": 0.0,
                "spy_final_equity": round(
                    initial_capital,
                    2,
                ),
                "portfolio_alpha": 0.0,
            },
        }

    eligible_predictions = [
        prediction
        for prediction in predictions
        if (
            _normalize_direction(
                getattr(
                    prediction,
                    "predicted_direction",
                    None,
                )
            )
            in {"Bullish", "Bearish"}
            and getattr(
                prediction,
                "stock_return",
                None,
            ) is not None
            and getattr(
                prediction,
                "created_at",
                None,
            ) is not None
            and getattr(
                prediction,
                "evaluation_market_date",
                None,
            ) is not None
        )
    ]

    eligible_predictions.sort(
        key=lambda prediction: (
            getattr(
                prediction,
                "created_at",
            ),
            getattr(
                prediction,
                "id",
                0,
            ) or 0,
        )
    )

    if not eligible_predictions:
        return {
            "initial_capital": initial_capital,
            "final_equity": initial_capital,
            "realized_pnl": 0.0,
            "total_return": 0.0,
            "positions_taken": 0,
            "positions_skipped": 0,
            "winning_positions": 0,
            "losing_positions": 0,
            "flat_positions": 0,
            "win_rate": 0.0,
            "max_drawdown": 0.0,
            "benchmark": {
                "spy_start_price": None,
                "spy_end_price": None,
                "spy_return": 0.0,
                "spy_final_equity": round(
                    initial_capital,
                    2,
                ),
                "portfolio_alpha": 0.0,
            },
        }

    cash = initial_capital
    realized_pnl = 0.0

    positions_taken = 0
    positions_skipped = 0
    winning_positions = 0
    losing_positions = 0
    flat_positions = 0

    open_positions: list[dict] = []

    peak_equity = initial_capital
    max_drawdown = 0.0

    predictions_by_date: dict = {}

    for prediction in eligible_predictions:
        entry_date = _as_date(
            getattr(
                prediction,
                "created_at",
            )
        )

        predictions_by_date.setdefault(
            entry_date,
            [],
        ).append(
            prediction
        )

    event_dates = {
        _as_date(
            getattr(
                prediction,
                "created_at",
            )
        )
        for prediction in eligible_predictions
    }

    event_dates.update(
        _as_date(
            getattr(
                prediction,
                "evaluation_market_date",
            )
        )
        for prediction in eligible_predictions
    )

    for current_date in sorted(
        event_dates
    ):
        positions_to_close = [
            position
            for position in open_positions
            if (
                position["exit_date"]
                <= current_date
            )
        ]

        for position in positions_to_close:
            pnl = position["pnl"]

            cash += (
                position_size
                + pnl
            )

            realized_pnl += pnl

            if pnl > 0:
                winning_positions += 1
            elif pnl < 0:
                losing_positions += 1
            else:
                flat_positions += 1

            open_positions.remove(
                position
            )

            realized_equity = (
                cash
                + (
                    len(open_positions)
                    * position_size
                )
            )

            peak_equity = max(
                peak_equity,
                realized_equity,
            )

            drawdown = (
                realized_equity
                / peak_equity
                - 1.0
            )

            max_drawdown = min(
                max_drawdown,
                drawdown,
            )

        daily_predictions = (
            predictions_by_date.get(
                current_date,
                [],
            )
        )

        for prediction in daily_predictions:
            if (
                len(open_positions)
                >= max_open_positions
            ):
                positions_skipped += 1
                continue

            if cash < position_size:
                positions_skipped += 1
                continue

            pnl = calculate_position_pnl(
                predicted_direction=(
                    prediction.predicted_direction
                ),
                stock_return=(
                    prediction.stock_return
                ),
                position_size=position_size,
            )

            cash -= position_size

            open_positions.append({
                "prediction_id": getattr(
                    prediction,
                    "id",
                    None,
                ),
                "ticker": getattr(
                    prediction,
                    "ticker",
                    None,
                ),
                "entry_date": current_date,
                "exit_date": _as_date(
                    getattr(
                        prediction,
                        "evaluation_market_date",
                    )
                ),
                "pnl": pnl,
            })

            positions_taken += 1

    assert not open_positions

    final_equity = cash

    total_return = (
        (
            final_equity
            / initial_capital
            - 1.0
        )
        * 100
    )

    closed_positions = (
        winning_positions
        + losing_positions
        + flat_positions
    )

    win_rate = (
        winning_positions
        / closed_positions
        * 100
        if closed_positions > 0
        else 0.0
    )

    benchmark = calculate_spy_benchmark(
        eligible_predictions,
        initial_capital=initial_capital,
    )

    portfolio_alpha = (
        total_return
        - benchmark["spy_return"]
    )

    benchmark[
        "portfolio_alpha"
    ] = round(
        portfolio_alpha,
        2,
    )

    return {
        "initial_capital": round(
            initial_capital,
            2,
        ),
        "final_equity": round(
            final_equity,
            2,
        ),
        "realized_pnl": round(
            realized_pnl,
            2,
        ),
        "total_return": round(
            total_return,
            2,
        ),
        "positions_taken": positions_taken,
        "positions_skipped": positions_skipped,
        "winning_positions": winning_positions,
        "losing_positions": losing_positions,
        "flat_positions": flat_positions,
        "win_rate": round(
            win_rate,
            2,
        ),
        "max_drawdown": round(
            max_drawdown * 100,
            2,
        ),
        "benchmark": benchmark,
    }


def _as_date(
    value: datetime,
):
    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    return value
