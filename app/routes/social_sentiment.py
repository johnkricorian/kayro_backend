from fastapi import APIRouter

from app.services.social_sentiment import (
    get_social_sentiment,
)

router = APIRouter(
    prefix="/social-sentiment",
    tags=["Social Sentiment"]
)

@router.get("/{ticker}")
def social_sentiment(
    ticker: str
):
    return get_social_sentiment(ticker=ticker)
