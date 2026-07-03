from app.services.sentiment import analyze_news_sentiment
from app.services.market import fetch_market_data
from app.services.technical import compute_technical_analysis
from app.services.ml import train_and_predict
from app.services import score_cache
from app.database.prediction_repository import save_prediction
from app.core.logger import create_logger

logger = create_logger(__name__)

def clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min(float(value), max_value), min_value)


def build_stock_score(ticker: str, forecast_horizon: int = 15) -> dict:
    ticker = ticker.upper()

    cached = score_cache.get(
        ticker=ticker,
        forecast_horizon=forecast_horizon
    )

    if cached is not None:
        logger.info(f"⚡ Score cache hit {ticker}")
        return cached

    sentiment = analyze_news_sentiment(ticker)

    market_df = fetch_market_data(ticker)
    technical = compute_technical_analysis(market_df)

    ml = train_and_predict(
        ticker=ticker,
        forecast_horizon=forecast_horizon
    )

    signals = build_signals(
        sentiment=sentiment,
        technical=technical,
        ml=ml
    )

    kayro_score = compute_kayro_score(signals)

    result = {
        "ticker": ticker,
        "kayro_score": kayro_score,
        "recommendation": recommendation_label(kayro_score),
        "confidence": ml["prediction"]["confidence"],
        "signals": signals,
        "sentiment": sentiment,
        "technical": technical,
        "prediction": ml["prediction"],
        "model": ml["model"],
        "market_context": ml["market_context"],
        "backtest": ml["backtest"],
        "top_features": ml["top_features"],
        "disclaimer": "This prediction is for informational purposes only and is not financial advice."
    }

    save_prediction(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
        predicted_direction=ml["prediction"]["direction"],
        probability_up=ml["prediction"]["probability_up"],
        confidence=ml["prediction"]["confidence"],
        kayro_score=kayro_score,
        recommendation=recommendation_label(kayro_score),
        price_at_prediction=ml["market_context"]["latest_close"],
    )

    score_cache.set(
        ticker=ticker,
        forecast_horizon=forecast_horizon,
        value=result
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
    confidence = ml["prediction"].get("confidence", 0)
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


def compute_kayro_score(signals: list[dict]) -> int:
    raw_score = 50 + sum(item["impact"] for item in signals)

    return round(clamp(raw_score, 0, 100))


def recommendation_label(score: int) -> str:
    if score >= 80:
        return "Strong Buy"
    if score >= 65:
        return "Buy"
    if score >= 50:
        return "Watch"
    if score >= 35:
        return "Weak"
    return "Avoid"
