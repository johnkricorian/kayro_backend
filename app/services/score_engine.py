from app.services.sentiment import get_news_sentiment
from app.services.market import fetch_market_data
from app.services.technical import compute_technical_analysis
from app.services.ml import train_and_predict
from app.services import score_cache
from app.database.prediction_repository import save_prediction
from app.core.logger import create_logger
from app.services.company_logo import build_company_logo_url
from app.services.market_score import compute_market_score

logger = create_logger(__name__)

def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min(float(value), max_value), min_value)

def build_stock_score(
    ticker: str,
    forecast_horizon: int = 15
) -> dict:
    ticker = ticker.upper()

    cached = score_cache.get(
        ticker=ticker,
        forecast_horizon=forecast_horizon
    )

    if cached is not None:
        logger.info(
            "Score cache hit for %s",
            ticker
        )
        return cached

    # NEWS / FINBERT
    sentiment = get_news_sentiment(
        ticker=ticker,
        limit=10,
    )

    # MARKET DATA
    market_df = fetch_market_data(
        ticker
    )

    price_history = build_price_history(
        market_df=market_df,
        limit=10,
    )

    # TECHNICAL ANALYSIS
    technical = compute_technical_analysis(
        market_df
    )

    # MACHINE LEARNING
    ml = train_and_predict(
        ticker=ticker,
        forecast_horizon=forecast_horizon
    )

    prediction = ml["prediction"]
    market_context = ml["market_context"]

    latest_close = float(
        market_context["latest_close"]
    )

        # Capture SPY at prediction time.
    spy_df = fetch_market_data(
        "SPY"
    )

    spy_entry_price = float(
        spy_df["Close"].iloc[-1]
    )

    # TARGET PRICE
    prediction["target"] = compute_target_price(
        latest_close=latest_close,
        probability_up=prediction["probability_up"],
        probability_down=prediction["probability_down"],
        forecast_horizon=forecast_horizon,
    )

    # SIGNALS
    signals = build_signals(
        sentiment=sentiment,
        technical=technical,
        ml=ml,
    )

    # COMPONENT SCORES
    finbert_score = float(
        sentiment.get(
            "score",
            0.0
        )
    )

    technical_score = float(
        technical.get(
            "technical_score",
            0.0
        )
    )

    probability_up = float(
        prediction.get(
            "probability_up",
            50.0
        )
    )

    market = compute_market_score()

    market_score = float(
        market["score"]
    )

    kayro_score = compute_kayro_score(
        signals=signals,
        direction=prediction["direction"],
    )

    recommendation = recommendation_label(
        score=kayro_score,
        direction=prediction["direction"],
    )

    result = {
        "ticker": ticker,
        "logo_url": build_company_logo_url(
            ticker
        ),
        "kayro_score": kayro_score,
        "recommendation": recommendation,
        "confidence": prediction["direction_confidence"],
        "signals": signals,
        "sentiment": sentiment,
        "technical": technical,
        "prediction": prediction,
        "model": ml["model"],
        "market_context": market_context,
        "backtest": ml["backtest"],
        "top_features": ml["top_features"],
        "price_history": price_history,
        "disclaimer": (
            "This prediction is for informational purposes only "
            "and is not financial advice."
        ),
    }

    save_prediction(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
        predicted_direction=prediction["direction"],
        probability_up=prediction["probability_up"],
        direction_confidence=prediction["direction_confidence"],
        qeyro_score=kayro_score,
        recommendation=recommendation,
        target_price=prediction["target"],
        price_at_prediction=latest_close,
        spy_entry_price=spy_entry_price,
        technical_score=technical_score,
        news_score=finbert_score,
        market_score=market_score,
    )

    score_cache.set(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
        value=result,
    )

    return result

def build_signals(
    sentiment: dict,
    technical: dict,
    ml: dict
) -> list[dict]:

    signals = []

    finbert_score = sentiment.get("finbert_score", 0)
    alpha_score = sentiment.get("alpha_score", 0)
    media_buzz = sentiment.get("media_buzz", 0)

    technical_score = technical.get("technical_score", 0)
    rsi = technical.get("rsi")
    trend = technical.get("trend")
    macd_histogram = technical.get("macd_histogram")
    momentum_20d = technical.get("momentum_20d", 0)

    probability_up = ml["prediction"].get("probability_up", 0)
    confidence = ml["prediction"].get(
        "direction_confidence",
        0,
    )
    reliability = ml["model"].get("reliability_score", 0)

    # News / sentiment
    if finbert_score > 0.25:
        signals.append(signal("AI News", "Positive financial news sentiment", 18, "news"))
    elif finbert_score < -0.25:
        signals.append(signal("AI News", "Negative financial news sentiment", -18, "news"))

    if alpha_score > 0.25:
        signals.append(signal("Market News", "Alpha Vantage sentiment is positive", 10, "news"))
    elif alpha_score < -0.25:
        signals.append(signal("Market News", "Alpha Vantage sentiment is negative", -10, "news"))

    if media_buzz >= 0.6:
        signals.append(signal("Media Buzz", "High media coverage detected", 8, "news"))
    elif media_buzz >= 0.3:
        signals.append(signal("Media Buzz", "Rising media attention", 5, "news"))

    # Technical
    if technical_score > 0.35:
        signals.append(signal("Technical", "Strong technical setup", 16, "technical"))
    elif technical_score > 0.15:
        signals.append(signal("Technical", "Improving technical setup", 10, "technical"))
    elif technical_score < -0.25:
        signals.append(signal("Technical", "Weak technical setup", -12, "technical"))

    if trend == "Bullish":
        signals.append(signal("Trend", "EMA trend is bullish", 12, "technical"))
    elif trend == "Bearish":
        signals.append(signal("Trend", "EMA trend is bearish", -12, "technical"))

    if macd_histogram is not None and macd_histogram > 0:
        signals.append(signal("MACD", "Bullish MACD momentum", 8, "technical"))
    elif macd_histogram is not None and macd_histogram < 0:
        signals.append(signal("MACD", "Bearish MACD momentum", -8, "technical"))

    if rsi is not None and rsi > 70:
        signals.append(signal("RSI", "RSI is overbought", -6, "technical"))
    elif rsi is not None and rsi < 30:
        signals.append(signal("RSI", "RSI is oversold", 6, "technical"))

    if momentum_20d > 5:
        signals.append(signal("Momentum", "Positive 20-day momentum", 9, "technical"))
    elif momentum_20d < -5:
        signals.append(signal("Momentum", "Negative 20-day momentum", -9, "technical"))

    # ML
    if probability_up >= 70:
        signals.append(signal("Machine Learning", "Model predicts strong upside", 24, "ml"))
    elif probability_up >= 60:
        signals.append(signal("Machine Learning", "Model predicts upside", 18, "ml"))
    elif probability_up <= 35:
        signals.append(signal("Machine Learning", "Model predicts downside", -18, "ml"))

    if confidence >= 75:
        signals.append(signal("Confidence", "High prediction confidence", 10, "ml"))
    elif confidence < 55:
        signals.append(signal("Confidence", "Low prediction confidence", -6, "ml"))

    if reliability >= 60:
        signals.append(signal("Reliability", "Model reliability is strong", 10, "ml"))
    elif reliability < 52:
        signals.append(signal("Reliability", "Model reliability is weak", -8, "ml"))

    if not signals:
        signals.append(signal("Neutral", "No strong directional signal detected", 0, "neutral"))

    return signals

def signal(
    title: str,
    description: str,
    impact: int,
    category: str
) -> dict:
    return {
        "title": title,
        "description": description,
        "impact": impact,
        "category": category,
        "direction": "positive" if impact > 0 else "negative" if impact < 0 else "neutral"
    }

def compute_kayro_score(
    signals: list[dict],
    direction: str,
) -> int:
    direction = direction.lower()

    directional_impacts = []
    quality_impacts = []

    for item in signals:
        impact = item["impact"]
        category = item["category"]

        if category in {"technical", "ml", "news"}:
            directional_impacts.append(impact)
        else:
            quality_impacts.append(abs(impact))

    directional_score = sum(directional_impacts)

    if direction in {"bearish", "strong bearish"}:
        directional_score *= -1
    elif direction not in {"bullish", "strong bullish"}:
        directional_score = 0

    raw_score = (
        50
        + directional_score
        + sum(quality_impacts)
    )

    return round(clamp(raw_score, 0, 100))

def recommendation_label(
    score: int,
    direction: str,
) -> str:
    direction = direction.lower()

    if direction in {"bullish", "strong bullish"}:
        if score >= 80:
            return "Strong Buy"
        if score >= 65:
            return "Buy"
        if score >= 50:
            return "Watch"
        return "Avoid"

    if direction in {"bearish", "strong bearish"}:
        if score >= 80:
            return "Strong Sell"
        if score >= 65:
            return "Sell"
        if score >= 50:
            return "Watch"
        return "Avoid"

    return "Watch"

import pandas as pd

def build_price_history(
    market_df: pd.DataFrame,
    limit: int = 10,
) -> list[dict]:
    if market_df is None or market_df.empty:
        return []

    if "Close" not in market_df.columns:
        return []

    history = (
        market_df
        .dropna(subset=["Close"])
        .tail(limit)
    )

    return [
        {
            "date": index.strftime("%Y-%m-%d"),
            "close": round(float(row["Close"]), 2),
        }
        for index, row in history.iterrows()
    ]

def compute_target_price(
    latest_close: float,
    probability_up: float,
    probability_down: float,
    forecast_horizon: int,
) -> float:
    if latest_close <= 0:
        return 0.0

    up = probability_up / 100 if probability_up > 1 else probability_up
    down = (
        probability_down / 100
        if probability_down > 1
        else probability_down
    )

    probability_edge = up - down
    horizon_factor = max(forecast_horizon, 1) / 15

    # Amplitude maximale indicative de 8 % sur 15 jours.
    expected_return = 0.08 * probability_edge * horizon_factor
    target = latest_close * (1 + expected_return)

    return round(max(target, 0), 2)
