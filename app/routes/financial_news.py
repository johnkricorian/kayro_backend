from fastapi import APIRouter, Query

from app.services.financial_news import (
    get_stock_news,
)

router = APIRouter(
    prefix="/news",
    tags=["Financial News"]
)


@router.get("/{ticker}")
def stock_news(
    ticker: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    )
):
    return get_stock_news(
        ticker=ticker,
        limit=limit
    )
