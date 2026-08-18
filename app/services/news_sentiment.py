from app.services.financial_news import get_stock_news
from app.services.finbert import finbert_score

def get_news_sentiment(
    ticker: str,
    limit: int = 20
) -> dict:
    ticker = ticker.upper()

    articles = get_stock_news(
        ticker=ticker,
        limit=limit
    )

    if not articles:
        return {
            "ticker": ticker,
            "score": 0.0,
            "label": "Neutral",
            "articles_count": 0,
            "articles": [],
        }

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
            "finbert_score": round(score, 4),
            "finbert_label": label,
        })

    if not scored_articles:
        return {
            "ticker": ticker,
            "score": 0.0,
            "label": "Neutral",
            "articles_count": 0,
            "articles": [],
        }

    average_score = sum(
        article["finbert_score"]
        for article in scored_articles
    ) / len(scored_articles)

    return {
        "ticker": ticker,
        "score": round(average_score, 4),
        "label": sentiment_label(average_score),
        "articles_count": len(scored_articles),
        "articles": scored_articles,
    }

def sentiment_label(
    score: float
) -> str:
    if score >= 0.15:
        return "Positive"

    if score <= -0.15:
        return "Negative"

    return "Neutral"
