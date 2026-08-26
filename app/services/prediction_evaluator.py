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

    # SPY is our US trading-session calendar
    # and our market benchmark.
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

            # Not enough US trading sessions
            # have elapsed yet.
            if evaluation_dates is None:
                skipped += 1
                continue

            entry_date, exit_date = (
                evaluation_dates
            )

            # Stock market data.
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
                    f"No market data for "
                    f"{prediction.ticker}"
                )

            # Stock exit price:
            # exactly on the same exit session
            # determined from SPY.
            stock_exit_price = get_close_on_date(
                df=stock_df,
                date=exit_date,
            )

            if stock_exit_price is None:
                raise ValueError(
                    f"No {prediction.ticker} price "
                    f"for evaluation date "
                    f"{exit_date.date()}"
                )

            # Stock entry price was captured
            # when the prediction was created.
            if (
                prediction.price_at_prediction
                is None
                or prediction.price_at_prediction <= 0
            ):
                raise ValueError(
                    "Missing price_at_prediction"
                )

            start_price = float(
                prediction.price_at_prediction
            )

            # SPY ENTRY PRICE
            #
            # New predictions:
            # use the SPY value captured at T0.
            #
            # Legacy predictions:
            # reconstruct the SPY close from the
            # entry trading session.
            if (
                prediction.spy_entry_price
                is not None
                and prediction.spy_entry_price > 0
            ):
                spy_entry_price = float(
                    prediction.spy_entry_price
                )

            else:
                spy_entry_price = (
                    get_close_on_date(
                        df=spy_df,
                        date=entry_date,
                    )
                )

                if (
                    spy_entry_price is None
                    or spy_entry_price <= 0
                ):
                    raise ValueError(
                        f"No SPY entry price for "
                        f"{entry_date.date()}"
                    )

            # SPY exit price must use exactly
            # the same market session as the stock.
            spy_exit_price = get_close_on_date(
                df=spy_df,
                date=exit_date,
            )

            if (
                spy_exit_price is None
                or spy_exit_price <= 0
            ):
                raise ValueError(
                    f"No SPY exit price for "
                    f"{exit_date.date()}"
                )

            # Stock return.
            stock_return = (
                stock_exit_price
                / start_price
                - 1.0
            )

            # SPY return over the same period.
            spy_return = (
                spy_exit_price
                / spy_entry_price
                - 1.0
            )

            # Relative performance versus SPY.
            alpha = (
                stock_return
                - spy_return
            )

            # Actual stock direction.
            actual_direction = (
                get_actual_direction(
                    stock_return
                )
            )

            # Directional correctness.
            prediction_correct = (
                is_prediction_correct(
                    predicted_direction=(
                        prediction
                        .predicted_direction
                    ),
                    start_price=start_price,
                    end_price=stock_exit_price,
                )
            )

            # Short return is intentionally
            # separate from alpha.
            short_return = None

            if is_bearish_prediction(
                prediction.predicted_direction
            ):
                short_return = (
                    -stock_return
                )

            # Persist only evaluation results.
            #
            # spy_entry_price is deliberately
            # NOT modified here.
            updated = update_prediction_result(
                prediction_id=prediction.id,
                price_after_horizon=round(
                    stock_exit_price,
                    4,
                ),
                prediction_correct=(
                    prediction_correct
                ),
                actual_direction=(
                    actual_direction
                ),
                stock_return=round(
                    stock_return,
                    6,
                ),
                spy_exit_price=round(
                    spy_exit_price,
                    4,
                ),
                spy_return=round(
                    spy_return,
                    6,
                ),
                alpha=round(
                    alpha,
                    6,
                ),
                short_return=(
                    round(
                        short_return,
                        6,
                    )
                    if short_return
                    is not None
                    else None
                ),
                evaluation_market_date=(
                    exit_date.to_pydatetime()
                ),
            )

            if updated:
                evaluated += 1
            else:
                # Another execution already
                # evaluated this prediction.
                skipped += 1

        except Exception as error:
            errors.append({
                "prediction_id": (
                    prediction.id
                ),
                "ticker": (
                    prediction.ticker
                ),
                "forecast_horizon": (
                    prediction.forecast_horizon
                ),
                "error": str(error),
            })

    return {
        "pending": len(predictions),
        "evaluated": evaluated,
        "skipped": skipped,
        "errors": errors,
    }


def prepare_market_dataframe(
    df: pd.DataFrame | None,
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
            subset=[
                "Date",
                "Close",
            ]
        )
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


def get_evaluation_dates(
    spy_df: pd.DataFrame,
    created_at: datetime,
    forecast_horizon: int,
) -> tuple[
    pd.Timestamp,
    pd.Timestamp,
] | None:
    if forecast_horizon <= 0:
        return None

    prediction_date = (
        pd.Timestamp(
            created_at
        )
        .tz_localize(None)
        .normalize()
    )

    # Last US trading session available
    # on or before prediction date.
    #
    # If prediction is created on a weekend
    # or US holiday, this automatically uses
    # the previous market session.
    entry_sessions = (
        spy_df[
            spy_df["Date"]
            .dt.normalize()
            <= prediction_date
        ]
        .sort_values("Date")
    )

    if entry_sessions.empty:
        return None

    entry_date = (
        entry_sessions
        .iloc[-1]["Date"]
        .normalize()
    )

    # SPY only contains real US market
    # sessions, therefore weekends and
    # exchange holidays are naturally
    # excluded.
    future_sessions = (
        spy_df[
            spy_df["Date"]
            .dt.normalize()
            > entry_date
        ]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    if (
        len(future_sessions)
        < forecast_horizon
    ):
        return None

    exit_date = (
        future_sessions
        .iloc[
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
        df["Date"]
        .dt.normalize()
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
    if (
        start_price is None
        or start_price <= 0
    ):
        return False

    direction = (
        predicted_direction.lower()
    )

    if "bullish" in direction:
        return (
            end_price > start_price
        )

    if "bearish" in direction:
        return (
            end_price < start_price
        )

    if "neutral" in direction:
        price_change = (
            end_price
            / start_price
            - 1.0
        )

        return (
            abs(price_change)
            <= NEUTRAL_THRESHOLD
        )

    return False

def get_pending_evaluation_stats() -> dict:
    predictions = get_pending_predictions()

    if not predictions:
        return {
            "pending_predictions": 0,
            "not_due_predictions": 0,
            "due_predictions": 0,
            "overdue_predictions": 0,
            "errors": [],
        }

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
            "pending_predictions": len(
                predictions
            ),
            "not_due_predictions": 0,
            "due_predictions": 0,
            "overdue_predictions": 0,
            "errors": [{
                "ticker": "SPY",
                "error": (
                    "SPY market data unavailable"
                ),
            }],
        }

    latest_market_date = (
        spy_df.iloc[-1]["Date"]
        .normalize()
    )

    not_due = 0
    due = 0
    overdue = 0
    errors = []

    for prediction in predictions:
        try:
            evaluation_dates = (
                get_evaluation_dates(
                    spy_df=spy_df,
                    created_at=(
                        prediction.created_at
                    ),
                    forecast_horizon=(
                        prediction.forecast_horizon
                    ),
                )
            )

            if evaluation_dates is None:
                not_due += 1
                continue

            _, exit_date = evaluation_dates

            exit_date = (
                exit_date.normalize()
            )

            if exit_date < latest_market_date:
                overdue += 1

            elif exit_date == latest_market_date:
                due += 1

            else:
                not_due += 1

        except Exception as error:
            errors.append({
                "prediction_id": (
                    prediction.id
                ),
                "ticker": (
                    prediction.ticker
                ),
                "forecast_horizon": (
                    prediction.forecast_horizon
                ),
                "error": str(error),
            })

    return {
        "pending_predictions": len(
            predictions
        ),
        "not_due_predictions": not_due,
        "due_predictions": due,
        "overdue_predictions": overdue,
        "latest_market_date": (
            latest_market_date
            .date()
            .isoformat()
        ),
        "errors": errors,
    }
