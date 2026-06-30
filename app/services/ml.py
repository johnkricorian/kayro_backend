import pandas as pd

from app.services.market import fetch_market_data
from app.services.model_loader import load_model


FEATURES = [
    "distance_ma20",
    "volatility_50",
    "distance_ma50",
    "trend_strength_20",
    "ma_ratio_20",
    "MACD_signal",
    "MACD",
    "trend_slope",
    "RSI",
    "volatility_10",
    "ma_ratio_10",
    "MACD_diff",
    "return_10",
    "trend_slope_50",
    "vol_regime"
]


def build_features(
    df: pd.DataFrame,
    forecast_horizon: int = 4
) -> pd.DataFrame:
    df = df.copy()

    df["future_close"] = df["Close"].shift(-forecast_horizon)
    df["target"] = (df["future_close"] > df["Close"] * 1.01).astype(int)

    df["return_1"] = df["Close"].pct_change(1)
    df["return_3"] = df["Close"].pct_change(3)
    df["return_5"] = df["Close"].pct_change(5)
    df["return_10"] = df["Close"].pct_change(10)

    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_20"] = df["Close"].rolling(20).mean()

    df["ma_ratio_10"] = df["Close"] / df["ma_10"]
    df["ma_ratio_20"] = df["Close"] / df["ma_20"]

    df["volatility_10"] = df["Close"].pct_change().rolling(10).std()
    df["volatility_50"] = df["Close"].pct_change().rolling(50).std()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_diff"] = df["MACD"] - df["MACD_signal"]

    df["trend_strength_20"] = df["Close"] / df["ma_20"]
    df["trend_slope"] = df["ma_20"].diff()
    df["distance_ma20"] = (df["Close"] - df["ma_20"]) / df["ma_20"]

    ma_50 = df["Close"].rolling(50).mean()
    df["trend_slope_50"] = ma_50.diff()
    df["distance_ma50"] = (df["Close"] - ma_50) / ma_50

    df["vol_regime"] = df["volatility_10"] / df["volatility_50"]

    df[FEATURES] = df[FEATURES].shift(1)

    return df.dropna().reset_index(drop=True)

def train_and_predict(
    ticker: str,
    forecast_horizon: int = 4
) -> dict:
    ticker = ticker.upper()

    df = fetch_market_data(
        ticker=ticker,
        period="5y",
        interval="1d"
    ).reset_index()

    if "Date" not in df.columns:
        df = df.rename(columns={"index": "Date"})

    df = build_features(
        df=df,
        forecast_horizon=forecast_horizon
    )

    if len(df) < 80:
        raise ValueError(
            f"Not enough data for {ticker}. Rows after feature engineering: {len(df)}"
        )

    bundle = load_model(forecast_horizon)

    model = bundle["model"]
    accuracy = float(bundle.get("accuracy", 0))
    training_samples = int(bundle.get("training_samples", 0))
    test_samples = int(bundle.get("test_samples", 0))
    backtest = bundle.get("backtest", {})
    feature_importances = bundle.get("feature_importances", {})

    X = df[FEATURES]

    latest_features = X.iloc[[-1]]
    latest_prediction = int(model.predict(latest_features)[0])
    latest_proba = model.predict_proba(latest_features)[0]

    probability_up = round(float(latest_proba[1]) * 100, 1)
    probability_down = round(float(latest_proba[0]) * 100, 1)
    confidence = round(float(max(latest_proba)) * 100, 1)

    latest_rsi = round(float(df.iloc[-1]["RSI"]), 1)
    latest_macd = float(df.iloc[-1]["MACD_diff"])
    latest_vol_regime = float(df.iloc[-1]["vol_regime"])

    return {
        "ticker": ticker,
        "prediction": {
            "direction": signal_label(probability_up),
            "probability_up": probability_up,
            "probability_down": probability_down,
            "confidence": confidence,
            "time_horizon_days": forecast_horizon,
            "target": latest_prediction
        },
        "model": {
            "name": "XGBoostClassifier",
            "version": "v1",
            "status": "loaded",
            "reliability_score": round(accuracy * 100, 1),
            "reliability_label": reliability_label(accuracy * 100),
            "training_samples": training_samples,
            "test_samples": test_samples,
            "features_count": len(FEATURES)
        },
        "market_context": {
            "rsi": latest_rsi,
            "macd_diff": round(latest_macd, 4),
            "volatility_regime": round(latest_vol_regime, 2),
            "latest_close": round(float(df.iloc[-1]["Close"]), 4),
            "latest_date": str(df.iloc[-1]["Date"].date())
        },
        "backtest": backtest,
        "top_features": [
            {
                "feature": feature,
                "importance": round(float(value), 4)
            }
            for feature, value in feature_importances.items()
        ],
        "disclaimer": "This prediction is for informational purposes only and is not financial advice."
    }

def reliability_label(score: float) -> str:
    if score >= 70:
        return "Exceptional"
    if score >= 60:
        return "Strong"
    if score >= 55:
        return "Good"
    if score >= 50:
        return "Fair"
        return "Weak"


def signal_label(probability_up: float) -> str:
    if probability_up >= 75:
        return "Strong Bullish"
    if probability_up >= 60:
        return "Bullish"
    if probability_up >= 45:
        return "Neutral"
    if probability_up >= 30:
        return "Bearish"
    return "Strong Bearish"
