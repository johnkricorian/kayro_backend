from app.services.news_sentiment import get_news_sentiment
from app.services.market import fetch_market_data
from app.services.technical import compute_technical_analysis
from app.services.ml import train_and_predict

def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(value, maximum))

def normalize_probability(value: float) -> float:
    if value > 1:
        value /= 100.0

    return clamp(value)

def normalize_finbert(value: float) -> float:
    return clamp((value + 1.0) / 2.0)

def recommendation_label(score: int) -> str:
    if score >= 80:
        return "Strong Buy"

    if score >= 65:
        return "Buy"

    if score >= 50:
        return "Watch"

    if score >= 35:
        return "Neutral"

    return "Avoid"


def build_qeyro_score(
    ticker: str,
    forecast_horizon: int = 15
) -> dict:
    ticker = ticker.upper()

    sentiment = get_news_sentiment(
        ticker=ticker,
        limit=10,
    )

    market_df = fetch_market_data(
        ticker
    )

    technical = compute_technical_analysis(
        market_df
    )

    ml = train_and_predict(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
    )

    technical_score = clamp(
        float(
            technical.get(
                "technical_score",
                0.0
            )
        )
    )

    probability_up = normalize_probability(
        float(
            ml["prediction"].get(
                "probability_up",
                50.0
            )
        )
    )

    finbert_score = normalize_finbert(
        float(
            sentiment.get(
                "score",
                0.0
            )
        )
    )

    market_score = 0.5

    global_score = (
        technical_score * 0.35
        + probability_up * 0.40
        + finbert_score * 0.15
        + market_score * 0.10
    )

    kayro_score = round(
        global_score * 100
    )

    return {
        "ticker": ticker,
        "kayro_score": kayro_score,
        "recommendation": recommendation_label(
            kayro_score
        ),
        "sentiment": sentiment,
        "technical": technical,
        "prediction": ml["prediction"],
        "market_context": ml["market_context"],
    }
