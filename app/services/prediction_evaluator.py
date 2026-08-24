from datetime import datetime

import pandas as pd

from app.database.prediction_repository import (
    get_pending_predictions,
    update_prediction_result,
)
from app.services.market import fetch_market_data


NEUTRAL_THRESHOLD = 0.02


def evaluate_pending_predictions() -> dict:
    predictions = get_pending_predictions()

    evaluated = 0
    skipped = 0
    errors = []

    if not predictions:
        return {
            "pending": 0,
            "evaluated": 0,
            "skipped": 0,
            "errors": [],
        }

    # SPY is our US trading-session calendar.
    spy_df = fetch_market_data(
        ticker="SPY",
        period="1y",
        interval="1d",
    )

    spy_df = prepare_market_dataframe(
        spy_df
    )

    if spy_df.empty:
        return {
            "pending": len(predictions),
            "evaluated": 0,
            "skipped": len(predictions),
            "errors": [{
                "ticker": "SPY",
                "error": "SPY market data unavailable",
            }],
        }

    for prediction in predictions:
        try:
            evaluation_dates = get_evaluation_dates(
                spy_df=spy_df,
                created_at=prediction.created_at,
                forecast_horizon=prediction.forecast_horizon,
            )

            # The required number of US trading sessions
            # has not elapsed yet.
            if evaluation_dates is None:
                skipped += 1
                continue

            entry_date, exit_date = evaluation_dates

            stock_df = fetch_market_data(
                ticker=prediction.ticker,
                period="1y",
                interval="1d",
            )

            stock_df = prepare_market_dataframe(
                stock_df
            )

            if stock_df.empty:
                raise ValueError(
                    f"No market data for {prediction.ticker}"
                )

            stock_exit_price = get_close_on_date(
                df=stock_df,
                date=exit_date,
            )

            if stock_exit_price is None:
                raise ValueError(
                    f"No {prediction.ticker} price for "
                    f"evaluation date {exit_date.date()}"
                )

            if (
                prediction.price_at_prediction is None
                or prediction.price_at_prediction <= 0
            ):
                raise ValueError(
                    "Missing price_at_prediction"
                )

            spy_entry_price = get_close_on_date(
                df=spy_df,
                date=entry_date,
            )

            spy_exit_price = get_close_on_date(
                df=spy_df,
                date=exit_date,
            )

            if spy_entry_price is None:
                raise ValueError(
                    f"No SPY entry price for "
                    f"{entry_date.date()}"
                )

            if spy_exit_price is None:
                raise ValueError(
                    f"No SPY exit price for "
                    f"{exit_date.date()}"
                )

            start_price = float(
                prediction.price_at_prediction
            )

            stock_return = (
                stock_exit_price
                / start_price
                - 1.0
            )

            spy_return = (
                spy_exit_price
                / spy_entry_price
                - 1.0
            )

            alpha = (
                stock_return
                - spy_return
            )

            actual_direction = get_actual_direction(
                stock_return
            )

            prediction_correct = is_prediction_correct(
                predicted_direction=prediction.predicted_direction,
                start_price=start_price,
                end_price=stock_exit_price,
            )

            short_return = None

            if is_bearish_prediction(
                prediction.predicted_direction
            ):
                short_return = -stock_return

            updated = update_prediction_result(
                prediction_id=prediction.id,
                price_after_horizon=round(
                    stock_exit_price,
                    4
                ),
                prediction_correct=prediction_correct,
                actual_direction=actual_direction,
                stock_return=round(
                    stock_return,
                    6
                ),
                spy_exit_price=round(
                    spy_exit_price,
                    4
                ),
                spy_return=round(
                    spy_return,
                    6
                ),
                alpha=round(
                    alpha,
                    6
                ),
                short_return=(
                    round(short_return, 6)
                    if short_return is not None
                    else None
                ),
                evaluation_market_date=exit_date.to_pydatetime(),
            )

            if updated:
                evaluated += 1
            else:
                # Already evaluated by another execution.
                skipped += 1

        except Exception as error:
            errors.append({
                "prediction_id": prediction.id,
                "ticker": prediction.ticker,
                "forecast_horizon": prediction.forecast_horizon,
                "error": str(error),
            })

    return {
        "pending": len(predictions),
        "evaluated": evaluated,
        "skipped": skipped,
        "errors": errors,
    }


def prepare_market_dataframe(
    df: pd.DataFrame | None
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "Date" not in df.columns:
        df = df.reset_index()

    if "Date" not in df.columns:
        return pd.DataFrame()

    df["Date"] = pd.to_datetime(
        df["Date"],
        utc=True,
        errors="coerce",
    ).dt.tz_localize(None)

    df = (
        df
        .dropna(
            subset=["Date", "Close"]
        )
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


def get_evaluation_dates(
    spy_df: pd.DataFrame,
    created_at: datetime,
    forecast_horizon: int,
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    if forecast_horizon <= 0:
        return None

    prediction_date = (
        pd.Timestamp(created_at)
        .tz_localize(None)
        .normalize()
    )

    # Last real US market session available
    # on or before the prediction date.
    entry_sessions = (
        spy_df[
            spy_df["Date"].dt.normalize()
            <= prediction_date
        ]
        .sort_values("Date")
    )

    if entry_sessions.empty:
        return None

    entry_date = (
        entry_sessions.iloc[-1]["Date"]
        .normalize()
    )

    # Because SPY trades only on US market sessions,
    # weekends and US market holidays disappear naturally.
    future_sessions = (
        spy_df[
            spy_df["Date"].dt.normalize()
            > entry_date
        ]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    if len(future_sessions) < forecast_horizon:
        return None

    exit_date = (
        future_sessions.iloc[
            forecast_horizon - 1
        ]["Date"]
        .normalize()
    )

    return (
        entry_date,
        exit_date,
    )


def get_close_on_date(
    df: pd.DataFrame,
    date: pd.Timestamp,
) -> float | None:
    rows = df[
        df["Date"].dt.normalize()
        == date.normalize()
    ]

    if rows.empty:
        return None

    return float(
        rows.iloc[-1]["Close"]
    )


def get_actual_direction(
    stock_return: float,
) -> str:
    if stock_return > 0:
        return "Bullish"

    if stock_return < 0:
        return "Bearish"

    return "Neutral"


def is_bearish_prediction(
    predicted_direction: str,
) -> bool:
    return (
        "bearish"
        in predicted_direction.lower()
    )


def is_prediction_correct(
    predicted_direction: str,
    start_price: float | None,
    end_price: float,
) -> bool:
    if start_price is None or start_price <= 0:
        return False

    direction = predicted_direction.lower()

    if "bullish" in direction:
        return end_price > start_price

    if "bearish" in direction:
        return end_price < start_price

    if "neutral" in direction:
        price_change = (
            end_price / start_price
        ) - 1.0

        return (
            abs(price_change)
            <= NEUTRAL_THRESHOLD
        )

    return False
