from app.services.score_engine import (
    compute_kayro_score,
    recommendation_label,
    build_signals,
)

def test_compute_kayro_score_bullish_positive():
    signals = [
        {"impact": 20, "category": "technical"},
        {"impact": 10, "category": "ml"},
        {"impact": -5, "category": "news"},
    ]

    assert compute_kayro_score(
        signals,
        direction="Bullish",
    ) == 75


def test_compute_kayro_score_bearish_positive():
    signals = [
        {"impact": -20, "category": "technical"},
        {"impact": -10, "category": "ml"},
        {"impact": 5, "category": "news"},
    ]

    assert compute_kayro_score(
        signals,
        direction="Bearish",
    ) == 75


def test_compute_kayro_score_clamped_max():
    signals = [
        {"impact": 80, "category": "technical"},
        {"impact": 50, "category": "ml"},
    ]

    assert compute_kayro_score(
        signals,
        direction="Bullish",
    ) == 100


def test_compute_kayro_score_clamped_min():
    signals = [
        {"impact": -80, "category": "technical"},
        {"impact": -50, "category": "ml"},
    ]

    assert compute_kayro_score(
        signals,
        direction="Bullish",
    ) == 0

def test_recommendation_label():
    # Bullish
    assert recommendation_label(85, "Bullish") == "Strong Buy"
    assert recommendation_label(70, "Bullish") == "Buy"
    assert recommendation_label(55, "Bullish") == "Watch"
    assert recommendation_label(20, "Bullish") == "Avoid"

    # Bearish
    assert recommendation_label(85, "Bearish") == "Strong Sell"
    assert recommendation_label(70, "Bearish") == "Sell"
    assert recommendation_label(55, "Bearish") == "Watch"
    assert recommendation_label(20, "Bearish") == "Avoid"

    # Strong directions
    assert recommendation_label(85, "Strong Bullish") == "Strong Buy"
    assert recommendation_label(85, "Strong Bearish") == "Strong Sell"

    # Neutral
    assert recommendation_label(90, "Neutral") == "Watch"
    assert recommendation_label(40, "Neutral") == "Watch"


def test_build_signals_positive_case():
    sentiment = {
        "finbert_score": 0.4,
        "alpha_score": 0.3,
        "media_buzz": 0.7,
    }

    technical = {
        "technical_score": 0.4,
        "rsi": 55,
        "trend": "Bullish",
        "macd_histogram": 1.2,
        "momentum_20d": 8,
    }

    ml = {
        "prediction": {
            "probability_up": 72,
            "confidence": 80,
        },
        "model": {
            "reliability_score": 65,
        },
    }

    signals = build_signals(
        sentiment=sentiment,
        technical=technical,
        ml=ml
    )

    titles = [signal["title"] for signal in signals]

    assert "AI News" in titles
    assert "Technical" in titles
    assert "Machine Learning" in titles
    assert "Confidence" in titles
    assert all("impact" in signal for signal in signals)


def test_build_signals_negative_case():
    sentiment = {
        "finbert_score": -0.4,
        "alpha_score": -0.3,
        "media_buzz": 0,
    }

    technical = {
        "technical_score": -0.4,
        "rsi": 75,
        "trend": "Bearish",
        "macd_histogram": -1.0,
        "momentum_20d": -8,
    }

    ml = {
        "prediction": {
            "probability_up": 30,
            "confidence": 50,
        },
        "model": {
            "reliability_score": 45,
        },
    }

    signals = build_signals(
        sentiment=sentiment,
        technical=technical,
        ml=ml
    )

    assert any(signal["impact"] < 0 for signal in signals)
    assert any(signal["direction"] == "negative" for signal in signals)
