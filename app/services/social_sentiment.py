from app.services.adanos_client import adanos_client

def get_social_sentiment(
    ticker: str
) -> dict:
    ticker = ticker.upper()

    raw = adanos_client.get(
        f"v1/stock/{ticker}"
    )

    return {
        "ticker": raw.get("ticker", ticker),
        "company_name": raw.get("company_name"),
        "found": raw.get("found", False),
        "buzz_score": raw.get("buzz_score"),
        "trend": raw.get("trend"),
        "mentions": raw.get("mentions"),
        "sentiment_score": raw.get("sentiment_score"),
        "bullish_pct": raw.get("bullish_pct"),
        "bearish_pct": raw.get("bearish_pct"),
        "unique_posts": raw.get("unique_posts"),
        "subreddit_count": raw.get("subreddit_count"),
        "total_upvotes": raw.get("total_upvotes"),
        "daily_trend": raw.get("daily_trend", []),
        "top_subreddits": raw.get("top_subreddits", []),
        "provider": "adanos",
    }

from app.services.adanos_client import adanos_client


def get_social_sentiment(
    ticker: str
) -> dict:
    ticker = ticker.upper()

    raw = adanos_client.get(
        f"v1/stock/{ticker}"
    )

    return {
        "ticker": raw.get("ticker", ticker),
        "company_name": raw.get("company_name"),
        "found": raw.get("found", False),
        "buzz_score": raw.get("buzz_score"),
        "trend": raw.get("trend"),
        "mentions": raw.get("mentions"),
        "sentiment_score": raw.get("sentiment_score"),
        "bullish_pct": raw.get("bullish_pct"),
        "bearish_pct": raw.get("bearish_pct"),
        "unique_posts": raw.get("unique_posts"),
        "subreddit_count": raw.get("subreddit_count"),
        "total_upvotes": raw.get("total_upvotes"),
        "daily_trend": raw.get("daily_trend", []),
        "top_subreddits": raw.get("top_subreddits", []),
        "provider": "adanos",
    }

def get_trending_stocks(
    limit: int = 50
) -> list[dict]:
    raw = adanos_client.get(
        "v1/trending",
        params={
            "limit": limit,
            "type": "stock",
        }
    )

    return raw
