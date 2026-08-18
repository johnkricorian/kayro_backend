from fastapi import APIRouter, Query

from app.services.news_sentiment import (
    get_news_sentiment,
)

router = APIRouter(
    prefix="/news-sentiment",
    tags=["News Sentiment"]
)

@router.get("/{ticker}")
def news_sentiment(
    ticker: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=50
    )
):
    return get_news_sentiment(
        ticker=ticker,
        limit=limit
    )
