from fastapi import APIRouter

from app.database.prediction_repository import get_global_stats
from app.database.prediction_repository import get_global_stats, get_ticker_stats


router = APIRouter(
    prefix="/stats",
    tags=["Stats"]
)


@router.get("")
def stats():
    return get_global_stats()

@router.get("/{ticker}")
def ticker_stats(ticker: str):
    return get_ticker_stats(ticker)
