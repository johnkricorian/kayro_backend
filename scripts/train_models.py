from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.market import fetch_market_data
from app.services.ml import FEATURES, build_features
from app.services.sector_loader import load_sectors
from app.services.training_loader import load_training_stocks
from app.core.logger import create_logger

logger = create_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "app" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = [4, 7, 15, 30]


def load_one_stock(
    ticker: str,
    forecast_horizon: int,
    period: str
) -> pd.DataFrame | None:

    try:
        logger.info(f"📈 Fetching {ticker}...")

        df = fetch_market_data(
            ticker=ticker,
            period=period,
            interval="1d"
        ).reset_index()

        if "Date" not in df.columns:
            df = df.rename(columns={"index": "Date"})

        df = build_features(
            df=df,
            forecast_horizon=forecast_horizon
        )

        if len(df) < 500:
            logger.info(f"⚠️ {ticker}: only {len(df)} rows")
            return None

        df["ticker"] = ticker

        logger.info(f"✅ {ticker}: {len(df)} rows")

        return df

    except Exception as error:
        logger.info(f"❌ {ticker}: {error}")
        return None

def unique_training_stocks() -> list[dict]:
    sectors = load_sectors()

    seen = set()
    stocks = []

    for sector_stocks in sectors.values():
        for stock in sector_stocks:
            ticker = stock["ticker"]

            if ticker not in seen:
                seen.add(ticker)
                stocks.append(stock)

    return stocks

def build_training_dataset(
    forecast_horizon: int,
    period: str = "10y"
) -> pd.DataFrame:

    tickers = load_training_stocks()

    if not tickers:
        raise RuntimeError("training_stocks.json is empty.")

    rows = []

    logger.info(f"\n🚀 Loading {len(tickers)} stocks in parallel...\n")

    max_workers = min(16, len(tickers))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        futures = {
            executor.submit(
                load_one_stock,
                ticker,
                forecast_horizon,
                period
            ): ticker
            for ticker in tickers
        }

        completed = 0

        for future in as_completed(futures):

            ticker = futures[future]
            completed += 1

            try:
                result = future.result()

                if result is not None:
                    rows.append(result)

            except Exception as error:
                logger.info(f"❌ {ticker}: {error}")

            print(
                f"[{completed}/{len(tickers)}] processed",
                end="\r",
                flush=True
            )

    if not rows:
        raise RuntimeError("No training data collected.")

    dataset = (
        pd.concat(rows, ignore_index=True)
        .dropna(subset=FEATURES + ["target"])
    )

    logger.info("✅ Training dataset ready")
    logger.info(f"Stocks loaded : {len(rows)}")
    logger.info(f"Rows          : {len(dataset):,}")

    return dataset

def train_model(forecast_horizon: int):
    logger.info(f"\n🚀 Training {forecast_horizon}d global model...")

    df = build_training_dataset(forecast_horizon)

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
    accuracy = accuracy_score(y_test, y_pred)

    feature_importances = (
        pd.Series(model.feature_importances_, index=FEATURES)
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
        "backtest": {
            "summary": "Backtest disabled for global model. Use a dedicated endpoint for per-ticker backtests."
        }
    }

    model_path = MODEL_DIR / f"xgboost_{forecast_horizon}d.joblib"

    dump(metadata, model_path)

    logger.info(
        f"✅ Saved {model_path.name} "
        f"accuracy={accuracy:.2%} "
        f"samples={len(df)}"
    )


def main():
    for horizon in HORIZONS:
        train_model(forecast_horizon=horizon)

if __name__ == "__main__":
    main()
