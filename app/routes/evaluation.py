from fastapi import APIRouter
from app.services.prediction_evaluator import evaluate_pending_predictions
from app.database.prediction_repository import (
    get_global_stats,
    get_horizon_stats,
    get_score_bucket_stats,
    get_ticker_stats,
    get_leaderboard,
)

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)

@router.post("/run")
def run_evaluation():
    return evaluate_pending_predictions()

@router.get("/stats")
def get_evaluation_stats() -> dict:
    return {
        "global": get_global_stats(),
        "by_horizon": get_horizon_stats(),
        "by_score_bucket": get_score_bucket_stats(),
    }

@router.get("/stats")
def get_evaluation_stats() -> dict:
    return {
        "global": get_global_stats(),
        "by_horizon": get_horizon_stats(),
        "by_score_bucket": get_score_bucket_stats(),
    }

@router.get("/ticker/{ticker}")
def get_evaluation_ticker(
    ticker: str
) -> dict:
    return get_ticker_stats(
        ticker
    )

@router.get("/leaderboard")
def get_evaluation_leaderboard(
    limit: int = 20
) -> list[dict]:
    return get_leaderboard(
        limit=limit
    )
