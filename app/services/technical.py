import pandas as pd

from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator


def clamp(value: float, min_value: float = -1, max_value: float = 1) -> float:
    return max(min(float(value), max_value), min_value)


def compute_technical_analysis(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 60:
        return {
            "technical_score": 0,
            "rsi": None,
            "macd": None,
            "macd_signal": None,
            "macd_histogram": None,
            "ema20": None,
            "ema50": None,
            "ema200": None,
            "trend": "Not enough data",
            "momentum_5d": 0,
            "momentum_20d": 0,
            "momentum_50d": 0
        }

    close = df["Close"]

    rsi_series = RSIIndicator(close=close, window=14).rsi()

    macd_indicator = MACD(close=close)
    macd_series = macd_indicator.macd()
    macd_signal_series = macd_indicator.macd_signal()
    macd_histogram_series = macd_indicator.macd_diff()

    ema20_series = EMAIndicator(close=close, window=20).ema_indicator()
    ema50_series = EMAIndicator(close=close, window=50).ema_indicator()
    ema200_series = EMAIndicator(close=close, window=200).ema_indicator()

    latest_close = float(close.iloc[-1])
    latest_rsi = float(rsi_series.iloc[-1])
    latest_macd = float(macd_series.iloc[-1])
    latest_macd_signal = float(macd_signal_series.iloc[-1])
    latest_macd_histogram = float(macd_histogram_series.iloc[-1])

    latest_ema20 = float(ema20_series.iloc[-1])
    latest_ema50 = float(ema50_series.iloc[-1])
    latest_ema200 = float(ema200_series.iloc[-1])

    momentum_5d = float((close.iloc[-1] / close.iloc[-5]) - 1)
    momentum_20d = float((close.iloc[-1] / close.iloc[-20]) - 1)
    momentum_50d = float((close.iloc[-1] / close.iloc[-50]) - 1)

    if latest_ema20 > latest_ema50 > latest_ema200:
        trend = "Bullish"
        trend_score = 0.45
    elif latest_ema20 < latest_ema50 < latest_ema200:
        trend = "Bearish"
        trend_score = -0.45
    else:
        trend = "Neutral"
        trend_score = 0

    if latest_rsi < 30:
        rsi_score = 0.45
    elif latest_rsi < 45:
        rsi_score = 0.15
    elif latest_rsi <= 60:
        rsi_score = 0.10
    elif latest_rsi <= 70:
        rsi_score = 0.20
    else:
        rsi_score = -0.35

    macd_score = clamp(latest_macd_histogram / max(latest_close * 0.01, 0.01))

    momentum_score = clamp(
        0.25 * momentum_5d * 5 +
        0.35 * momentum_20d * 3 +
        0.40 * momentum_50d * 2
    )

    technical_score = clamp(
        0.30 * trend_score +
        0.25 * rsi_score +
        0.25 * macd_score +
        0.20 * momentum_score
    )

    return {
        "technical_score": round(technical_score, 4),

        "rsi": round(latest_rsi, 2),

        "macd": round(latest_macd, 4),
        "macd_signal": round(latest_macd_signal, 4),
        "macd_histogram": round(latest_macd_histogram, 4),

        "ema20": round(latest_ema20, 2),
        "ema50": round(latest_ema50, 2),
        "ema200": round(latest_ema200, 2),

        "trend": trend,

        "momentum_5d": round(momentum_5d * 100, 2),
        "momentum_20d": round(momentum_20d * 100, 2),
        "momentum_50d": round(momentum_50d * 100, 2)
    }
