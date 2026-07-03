from app.services.score_engine import (
    compute_kayro_score,
    recommendation_label,
    build_signals,
)


def test_compute_kayro_score_positive():
    signals = [
        {"impact": 20},
        {"impact": 10},
        {"impact": -5},
    ]

    assert compute_kayro_score(signals) == 75


def test_compute_kayro_score_clamped_max():
    signals = [
        {"impact": 80},
        {"impact": 50},
    ]

    assert compute_kayro_score(signals) == 100


def test_compute_kayro_score_clamped_min():
    signals = [
        {"impact": -80},
        {"impact": -50},
    ]

    assert compute_kayro_score(signals) == 0


def test_recommendation_label():
    assert recommendation_label(85) == "Strong Buy"
    assert recommendation_label(70) == "Buy"
    assert recommendation_label(55) == "Watch"
    assert recommendation_label(40) == "Weak"
    assert recommendation_label(20) == "Avoid"


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
