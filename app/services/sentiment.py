import pandas as pd

from app.services.finbert import finbert_score
from app.services.news import fetch_news


def analyze_news_sentiment(ticker: str) -> dict:

    articles = fetch_news(ticker)

    if not articles:
        return {
            "alpha_score": 0,
            "finbert_score": 0,
            "media_buzz": 0,
            "articles": []
        }

    df = pd.DataFrame(articles)

    df["finbert_score"] = df.apply(
        lambda row: finbert_score(
            f"{row['title']}. {row['summary']}"
        )[0],
        axis=1
    )

    alpha_score = float(df["alpha_score"].mean())

    finbert = float(df["finbert_score"].mean())

    media_buzz = min(len(df) / 50, 1)

    top_articles = (
        df.sort_values(
            "finbert_score",
            ascending=False
        )
        .head(5)
        .to_dict("records")
    )

    return {
        "alpha_score": alpha_score,
        "finbert_score": finbert,
        "media_buzz": media_buzz,
        "articles": top_articles
    }
