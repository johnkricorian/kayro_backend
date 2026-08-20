import pandas as pd
from app.services.market import fetch_market_data

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(
        minimum,
        min(value, maximum)
    )


def compute_index_score(
    df: pd.DataFrame
) -> dict:
    if df is None or df.empty or len(df) < 200:
        return {
            "score": 0.5,
            "latest_close": None,
            "ma20": None,
            "ma50": None,
            "ma200": None,
            "momentum_20d": None,
            "volatility_20d": None,
        }

    close = df["Close"]

    latest_close = float(
        close.iloc[-1]
    )

    ma20 = float(
        close.rolling(20).mean().iloc[-1]
    )

    ma50 = float(
        close.rolling(50).mean().iloc[-1]
    )

    ma200 = float(
        close.rolling(200).mean().iloc[-1]
    )

    momentum_20d = float(
        latest_close / close.iloc[-20] - 1
    )

    daily_returns = close.pct_change()

    volatility_20d = float(
        daily_returns
        .rolling(20)
        .std()
        .iloc[-1]
    )

    score = 0.5

    # Price vs short-term trend
    if latest_close > ma20:
        score += 0.05
    else:
        score -= 0.05

    # Medium-term trend
    if ma20 > ma50:
        score += 0.08
    else:
        score -= 0.08

    # Long-term trend
    if ma50 > ma200:
        score += 0.12
    else:
        score -= 0.12

    # Momentum
    if momentum_20d >= 0.05:
        score += 0.10

    elif momentum_20d >= 0.02:
        score += 0.05

    elif momentum_20d <= -0.05:
        score -= 0.10

    elif momentum_20d <= -0.02:
        score -= 0.05

    # Volatility penalty
    if volatility_20d >= 0.03:
        score -= 0.10

    elif volatility_20d >= 0.02:
        score -= 0.05

    score = clamp(
        score
    )

    return {
        "score": round(
            score,
            4
        ),
        "latest_close": round(
            latest_close,
            2
        ),
        "ma20": round(
            ma20,
            2
        ),
        "ma50": round(
            ma50,
            2
        ),
        "ma200": round(
            ma200,
            2
        ),
        "momentum_20d": round(
            momentum_20d * 100,
            2
        ),
        "volatility_20d": round(
            volatility_20d * 100,
            2
        ),
    }


def compute_market_score() -> dict:
    spy_df = fetch_market_data(
        ticker="SPY",
        period="1y",
        interval="1d",
    )

    qqq_df = fetch_market_data(
        ticker="QQQ",
        period="1y",
        interval="1d",
    )

    spy = compute_index_score(
        spy_df
    )

    qqq = compute_index_score(
        qqq_df
    )

    spy_score = float(
        spy["score"]
    )

    qqq_score = float(
        qqq["score"]
    )

    market_score = clamp(
        spy_score * 0.50
        + qqq_score * 0.50
    )

    return {
        "score": round(
            market_score,
            4
        ),
        "regime": market_regime(
            market_score
        ),
        "spy": spy,
        "qqq": qqq,
    }


def market_regime(
    score: float
) -> str:
    if score >= 0.80:
        return "Strong Risk-On"

    if score >= 0.60:
        return "Risk-On"

    if score >= 0.40:
        return "Neutral"

    if score >= 0.20:
        return "Risk-Off"

    return "Strong Risk-Off"
