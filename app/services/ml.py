import json
import urllib.request
import pandas as pd

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from app.services.market import fetch_market_data

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

    df = fetch_market_data(
        ticker=ticker,
        period="5y",
        interval="1d"
    ).reset_index()

    if "Date" not in df.columns:
        df = df.rename(columns={"index": "Date"})

    df = build_features(df, forecast_horizon)
    if len(df) < 80:
        raise ValueError(
            f"Not enough data for {ticker}. Rows after feature engineering: {len(df)}"
        )
    X = df[FEATURES]
    y = df["target"]

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    model = XGBClassifier(
        n_estimators=1200,
        max_depth=5,
        learning_rate=0.01,
        subsample=0.9,
        colsample_bytree=0.9,
        gamma=1,
        reg_alpha=0.1,
        reg_lambda=1,
        random_state=42,
        n_jobs=-1,
        eval_metric="logloss"
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    accuracy_pct = round(float(accuracy) * 100, 1)

    latest_features = X.iloc[[-1]]
    latest_prediction = int(model.predict(latest_features)[0])
    latest_proba = model.predict_proba(latest_features)[0]

    probability_up = round(float(latest_proba[1]) * 100, 1)
    probability_down = round(float(latest_proba[0]) * 100, 1)
    confidence = round(float(max(latest_proba)) * 100, 1)

    importances = (
        pd.Series(model.feature_importances_, index=FEATURES)
        .sort_values(ascending=False)
        .head(10)
    )

    df_compare = df.iloc[split_index:].copy()
    df_compare["prediction"] = y_pred
    df_compare["actual"] = y_test.values
    df_compare["is_correct"] = df_compare["prediction"] == df_compare["actual"]
    df_compare["prediction_confidence"] = y_proba.max(axis=1) * 100

    backtest = build_backtest(df_compare, forecast_horizon)

    latest_rsi = round(float(df.iloc[-1]["RSI"]), 1)
    latest_macd = float(df.iloc[-1]["MACD_diff"])
    latest_vol_regime = float(df.iloc[-1]["vol_regime"])

    return {
        "ticker": ticker.upper(),
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
            "status": "trained",
            "reliability_score": accuracy_pct,
            "reliability_label": reliability_label(accuracy_pct),
            "training_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
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
            for feature, value in importances.items()
        ],
        "disclaimer": "This prediction is for informational purposes only and is not financial advice."
    }


def build_backtest(
    df_compare: pd.DataFrame,
    forecast_horizon: int
) -> dict:
    trades = df_compare[df_compare["prediction"] == 1].copy()

    if trades.empty:
        return {
            "win_rate": 0,
            "average_return": 0,
            "total_return": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "summary": "No trades were triggered by the model."
        }

    trades["trade_return"] = (
        trades["future_close"] - trades["Close"]
    ) / trades["Close"]

    trades["equity_curve"] = (1 + trades["trade_return"]).cumprod()

    wins = trades[trades["trade_return"] > 0]
    losses = trades[trades["trade_return"] <= 0]

    win_rate = len(wins) / len(trades) * 100
    average_return = trades["trade_return"].mean() * 100
    total_return = (trades["equity_curve"].iloc[-1] - 1) * 100

    gross_profit = wins["trade_return"].sum()
    gross_loss = abs(losses["trade_return"].sum())

    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999

    rolling_max = trades["equity_curve"].cummax()
    drawdown = (trades["equity_curve"] - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100

    return {
        "win_rate": round(float(win_rate), 1),
        "average_return": round(float(average_return), 2),
        "total_return": round(float(total_return), 2),
        "profit_factor": round(float(profit_factor), 2),
        "max_drawdown": round(float(max_drawdown), 2),
        "trades": int(len(trades)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "summary": (
            f"The model triggered {len(trades)} historical trades. "
            f"{round(win_rate, 1)}% were profitable, with an average return "
            f"of {round(average_return, 2)}% over {forecast_horizon} days."
        )
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
