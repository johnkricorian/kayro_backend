from app.services.sentiment import get_news_sentiment
from app.services.market import fetch_market_data
from app.services.technical import compute_technical_analysis
from app.services.ml import train_and_predict
from app.services.market_score import compute_market_score

TECHNICAL_WEIGHT = 0.35
ML_WEIGHT = 0.40
NEWS_WEIGHT = 0.15
MARKET_WEIGHT = 0.10

def build_qeyro_score(
    ticker: str,
    forecast_horizon: int = 15
) -> dict:
    ticker = ticker.upper()

    # 1. News sentiment
    sentiment = get_news_sentiment(
        ticker=ticker,
        limit=10,
    )

    # 2. Market data
    market_df = fetch_market_data(
        ticker
    )

    # 3. Technical analysis
    technical = compute_technical_analysis(
        market_df
    )

    # 4. ML prediction
    ml = train_and_predict(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
    )

    prediction = ml["prediction"]
    market_context = ml["market_context"]

    latest_close = float(
        market_context["latest_close"]
    )

    # 5. Target price
    prediction["target"] = compute_target_price(
        latest_close=latest_close,
        probability_up=prediction["probability_up"],
        probability_down=prediction["probability_down"],
        forecast_horizon=forecast_horizon,
    )

    # 6. Normalize individual scores
    technical_score = normalize_technical(
        float(
            technical.get(
                "technical_score",
                0.0
            )
        )
    )

    probability_up_score = normalize_probability(
        float(
            prediction.get(
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

    market = compute_market_score()
    market_score = float(
        market.get(
            "score",
            0.5
        )
    )

    # 7. Qeyro Score
    global_score = (
        technical_score * TECHNICAL_WEIGHT
        + probability_up_score * ML_WEIGHT
        + finbert_score * NEWS_WEIGHT
        + market_score * MARKET_WEIGHT
    )

    qeyro_score = round(
        clamp(global_score) * 100
    )

    recommendation = recommendation_label(
        qeyro_score
    )

    direction_confidence = float(
        prediction.get(
            "direction_confidence",
            0.0
        )
    )

    # 8. Score breakdown
    score_breakdown = {
        "technical": round(
            technical_score * 100
        ),
        "ml": round(
            probability_up_score * 100
        ),
        "news": round(
            finbert_score * 100
        ),
        "market": round(
            market_score * 100
        ),
    }

    weighted_breakdown = {
        "technical": round(
            technical_score
            * TECHNICAL_WEIGHT
            * 100,
            2
        ),
        "ml": round(
            probability_up_score
            * ML_WEIGHT
            * 100,
            2
        ),
        "news": round(
            finbert_score
            * NEWS_WEIGHT
            * 100,
            2
        ),
        "market": round(
            market_score
            * MARKET_WEIGHT
            * 100,
            2
        ),
    }

    # 9. API response
    return {
        "ticker": ticker,
        "qeyro_score": qeyro_score,
        "recommendation": recommendation,
        "direction_confidence": direction_confidence,
        "market": market,
        "score_breakdown": score_breakdown,
        "weighted_breakdown": weighted_breakdown,
        "sentiment": sentiment,
        "technical": technical,
        "prediction": prediction,
        "market_context": market_context,
    }

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0
) -> float:
    return max(
        minimum,
        min(maximum, value)
    )


def normalize_probability(
    probability: float
) -> float:
    return clamp(
        probability / 100.0
    )


def normalize_finbert(
    score: float
) -> float:
    """
    Convert FinBERT score from [-1, 1]
    to Qeyro scale [0, 1].
    """
    return clamp(
        (score + 1.0) / 2.0
    )


def recommendation_label(
    score: int
) -> str:
    if score >= 80:
        return "Strong Buy"

    if score >= 65:
        return "Buy"

    if score >= 50:
        return "Watch"

    if score >= 35:
        return "Neutral"

    return "Avoid"

def compute_target_price(
    latest_close: float,
    probability_up: float,
    probability_down: float,
    forecast_horizon: int,
) -> float:
    if latest_close <= 0:
        return 0.0

    if forecast_horizon <= 0:
        return round(latest_close, 2)

    # Converts probabilities from percentages to [0, 1]
    prob_up = probability_up / 100.0
    prob_down = probability_down / 100.0

    # Directional edge:
    # 51.1% up / 48.9% down -> +0.022
    directional_edge = prob_up - prob_down

    # Maximum expected move for a 15-day horizon.
    # Scales with sqrt(time) rather than linearly.
    base_move_15d = 0.10

    horizon_factor = (forecast_horizon / 15.0) ** 0.5

    expected_move = (
        directional_edge
        * base_move_15d
        * horizon_factor
    )

    target_price = latest_close * (1 + expected_move)

    return round(target_price, 2)

def normalize_technical(
    score: float
) -> float:
    """
    Convert technical score from [-1, 1]
    to Qeyro scale [0, 1].

    -1.0 -> 0.00
     0.0 -> 0.50
    +1.0 -> 1.00
    """
    return clamp(
        (score + 1.0) / 2.0
    )
