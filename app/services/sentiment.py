import pandas as pd

from app.services.finbert import finbert_score
from app.services.news import fetch_news
from app.services.finbert import finbert_score
from app.services.financial_news import get_stock_news

def sentiment_label(score: float) -> str:
    if score >= 0.15:
        return "Positive"

    if score <= -0.15:
        return "Negative"

    return "Neutral"


def calculate_media_buzz(
    articles_count: int
) -> float:
    """
    Normalize media coverage between 0 and 1.

    0 articles  -> 0.00
    5 articles  -> 0.25
    10 articles -> 0.50
    15 articles -> 0.75
    20+ articles -> 1.00
    """
    if articles_count <= 0:
        return 0.0

    return min(
        articles_count / 20.0,
        1.0
    )


def get_news_sentiment(
    ticker: str,
    limit: int = 20
) -> dict:
    ticker = ticker.upper()

    articles = get_stock_news(
        ticker=ticker,
        limit=limit
    )

    scored_articles = []

    for article in articles:
        title = article.get("title") or ""
        summary = article.get("summary") or ""

        text = f"{title}. {summary}".strip()

        if not text:
            continue

        score, label = finbert_score(text)

        scored_articles.append({
            **article,
            "finbert_score": round(
                float(score),
                4
            ),
            "finbert_label": label,
        })

    if not scored_articles:
        return {
            "ticker": ticker,
            "score": 0.0,
            "label": "Neutral",
            "media_buzz": 0.0,
            "articles_count": 0,
            "articles": [],
        }

    average_score = sum(
        article["finbert_score"]
        for article in scored_articles
    ) / len(scored_articles)

    media_buzz = calculate_media_buzz(
        len(scored_articles)
    )

    return {
        "ticker": ticker,
        "score": round(
            average_score,
            4
        ),
        "label": sentiment_label(
            average_score
        ),
        "media_buzz": round(
            media_buzz,
            4
        ),
        "articles_count": len(
            scored_articles
        ),
        "articles": scored_articles,
    }
