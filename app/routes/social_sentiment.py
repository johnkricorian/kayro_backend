from fastapi import APIRouter, Query

from app.services.social_sentiment import (
    get_social_sentiment,
    get_trending_stocks,
)


router = APIRouter(
    prefix="/social-sentiment",
    tags=["Social Sentiment"]
)

@router.get("/trending")
def trending(
    limit: int = Query(
        default=50,
        ge=1,
        le=100
    )
):
    return get_trending_stocks(
        limit=limit
    )


@router.get("/{ticker}")
def social_sentiment(
    ticker: str
):
    return get_social_sentiment(
        ticker=ticker
    )
