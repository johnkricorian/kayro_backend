import os
import requests

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def fetch_news(ticker: str) -> list[dict]:
    """
    Fetch the latest Alpha Vantage news for a ticker.
    """

    if not ALPHA_VANTAGE_API_KEY:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")

    response = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY
        },
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    articles = []

    for article in data.get("feed", []):

        articles.append({
            "title": article.get("title"),
            "summary": article.get("summary"),
            "source": article.get("source"),
            "url": article.get("url"),
            "published_at": article.get("time_published"),
            "alpha_score": float(
                article.get("overall_sentiment_score", 0)
            )
        })

    return articles
