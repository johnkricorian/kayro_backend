from fastapi import APIRouter

from app.services.prediction_evaluator import (
    evaluate_pending_predictions,
    get_pending_evaluation_stats,
)
from app.services.prediction_batch import (
    generate_prediction_batch,
)
from app.database.prediction_repository import (
    get_global_stats,
    get_horizon_stats,
    get_score_bucket_stats,
    get_ticker_stats,
    get_leaderboard,
    get_viability_stats,
)


router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


@router.post("/run")
def run_evaluation() -> dict:
    return evaluate_pending_predictions()

@router.get("/stats")
def get_evaluation_stats() -> dict:
    global_stats = get_global_stats()
    pending_evaluation = (
        get_pending_evaluation_stats()
    )
    horizon_stats = get_horizon_stats()
    score_bucket_stats = (
        get_score_bucket_stats()
    )
    viability_stats = get_viability_stats()

    return {
        "global": global_stats,
        "pending_evaluation": pending_evaluation,
        "by_horizon": horizon_stats,
        "by_score_bucket": score_bucket_stats,
        "viability": viability_stats,
    }


@router.get("/performance")
def get_performance() -> dict:
    viability = get_viability_stats()

    prospective = viability[
        "prospective_validation"
    ]

    portfolio = prospective[
        "portfolio"
    ]

    benchmark = portfolio[
        "benchmark"
    ]

    return {
        "performance": {
            "validation_start_date": (
                prospective[
                    "start_date"
                ]
            ),
            "status": (
                prospective[
                    "sample_maturity"
                ]
            ),
            "prospective": {
                "generated": (
                    prospective[
                        "generated_predictions"
                    ]
                ),
                "evaluated": (
                    prospective[
                        "evaluated_predictions"
                    ]
                ),
                "pending": (
                    prospective[
                        "pending_predictions"
                    ]
                ),
            },
            "directional_evaluated": (
                prospective[
                    "directional_predictions"
                ]
            ),
            "accuracy": (
                prospective[
                    "direction_accuracy"
                ]
            ),
            "confidence_interval_95": (
                prospective[
                    "confidence_interval_95"
                ]
            ),
            "progress": (
                prospective[
                    "progress"
                ]
            ),
            "portfolio": {
                "initial_capital": (
                    portfolio[
                        "initial_capital"
                    ]
                ),
                "current_capital": (
                    portfolio[
                        "final_equity"
                    ]
                ),
                "return": (
                    portfolio[
                        "total_return"
                    ]
                ),
                "realized_pnl": (
                    portfolio[
                        "realized_pnl"
                    ]
                ),
                "positions_taken": (
                    portfolio[
                        "positions_taken"
                    ]
                ),
                "win_rate": (
                    portfolio[
                        "win_rate"
                    ]
                ),
                "max_drawdown": (
                    portfolio[
                        "max_drawdown"
                    ]
                ),
            },
            "benchmark": {
                "name": "S&P 500",
                "return": (
                    benchmark[
                        "spy_return"
                    ]
                ),
                "capital": (
                    benchmark[
                        "spy_final_equity"
                    ]
                ),
                "excess_return_vs_spy": (
                    benchmark[
                        "portfolio_alpha"
                    ]
                ),
            },
        }
    }


@router.get("/ticker/{ticker}")
def get_evaluation_ticker(
    ticker: str,
) -> dict:
    return get_ticker_stats(
        ticker
    )


@router.get("/leaderboard")
def get_evaluation_leaderboard(
    limit: int = 20,
) -> list[dict]:
    return get_leaderboard(
        limit=limit
    )


@router.post("/generate-batch")
def generate_batch() -> dict:
    return generate_prediction_batch(
        force_refresh=True
    )
