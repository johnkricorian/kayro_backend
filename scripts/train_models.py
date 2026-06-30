from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

from app.services.market import fetch_market_data
from app.services.ml import (
    FEATURES,
    build_features,
    build_backtest
)

MODEL_DIR = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "models"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = [4, 7, 15, 30]


def train_model(
    ticker: str,
    forecast_horizon: int
):

    print(f"\n🚀 Training {forecast_horizon}d model...")

    df = fetch_market_data(
        ticker=ticker,
        period="10y",
        interval="1d"
    ).reset_index()

    if "Date" not in df.columns:
        df = df.rename(columns={"index": "Date"})

    df = build_features(
        df=df,
        forecast_horizon=forecast_horizon
    )

    if len(df) < 300:
        raise RuntimeError(
            f"Not enough training data ({len(df)} rows)"
        )

    X = df[FEATURES]
    y = df["target"]

    split = int(len(df) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

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

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    df_compare = df.iloc[split:].copy()

    df_compare["prediction"] = y_pred
    df_compare["actual"] = y_test.values
    df_compare["prediction_confidence"] = (
        y_proba.max(axis=1) * 100
    )

    backtest = build_backtest(
        df_compare=df_compare,
        forecast_horizon=forecast_horizon
    )

    feature_importances = (
        pd.Series(
            model.feature_importances_,
            index=FEATURES
        )
        .sort_values(ascending=False)
        .head(10)
        .to_dict()
    )

    metadata = {
        "model": model,
        "accuracy": accuracy,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features": FEATURES,
        "feature_importances": feature_importances,
        "backtest": backtest
    }

    model_path = (
        MODEL_DIR
        / f"xgboost_{forecast_horizon}d.joblib"
    )

    dump(
        metadata,
        model_path
    )

    print(
        f"✅ Saved {model_path.name} "
        f"(accuracy={accuracy:.2%})"
    )


def main():

    training_symbol = "SPY"

    print("======================================")
    print("      Kayro Model Trainer")
    print("======================================")

    for horizon in HORIZONS:
        train_model(
            ticker=training_symbol,
            forecast_horizon=horizon
        )

    print("\n🎉 All models successfully trained.")


if __name__ == "__main__":
    main()
