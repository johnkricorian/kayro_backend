from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from app.database.prediction_repository import get_next_prospective_evaluation
from app.services import prediction_evaluator
from app.services.prediction_evaluator import (
    get_scheduled_evaluation_date,
    get_next_prospective_evaluation,
)

def make_market_df(
    dates: list[str],
    closes: list[float],
) -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Close": closes,
    })


def make_prediction(
    *,
    prediction_id: int = 1,
    ticker: str = "MSFT",
    created_at: datetime = datetime(2026, 8, 17, 15, 0, 0),
    forecast_horizon: int = 4,
    predicted_direction: str = "Bullish",
    price_at_prediction: float = 100.0,
    spy_entry_price: float = 200.0,
    prediction_correct=None,
):
    return SimpleNamespace(
        id=prediction_id,
        ticker=ticker,
        created_at=created_at,
        forecast_horizon=forecast_horizon,
        predicted_direction=predicted_direction,
        price_at_prediction=price_at_prediction,
        spy_entry_price=spy_entry_price,
        prediction_correct=prediction_correct,
    )


@pytest.fixture
def spy_df() -> pd.DataFrame:
    return make_market_df(
        dates=[
            "2026-08-14",
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
            "2026-08-24",
        ],
        closes=[
            198.0,
            200.0,
            201.0,
            202.0,
            203.0,
            204.0,
            205.0,
        ],
    )


@pytest.fixture
def stock_df() -> pd.DataFrame:
    return make_market_df(
        dates=[
            "2026-08-14",
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
            "2026-08-24",
        ],
        closes=[
            98.0,
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
            105.0,
        ],
    )


def test_prediction_not_due_yet(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            21,
            15,
            0,
        ),
        forecast_horizon=4,
    )

    spy = make_market_df(
        dates=[
            "2026-08-21",
            "2026-08-24",
        ],
        closes=[
            200.0,
            201.0,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert result["pending"] == 1
    assert result["evaluated"] == 0
    assert result["skipped"] == 1
    assert result["errors"] == []


def test_prediction_due(
    monkeypatch,
    spy_df,
    stock_df,
):
    prediction = make_prediction(
        price_at_prediction=100.0,
        spy_entry_price=200.0,
    )

    saved = {}

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy_df

        return stock_df

    def fake_update(
        **kwargs,
    ):
        saved.update(kwargs)
        return True

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "update_prediction_result",
        fake_update,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert result["evaluated"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == []

    assert saved["price_after_horizon"] == 104.0
    assert saved["actual_direction"] == "Bullish"
    assert saved["prediction_correct"] is True


def test_weekend_is_not_counted_as_session():
    spy = make_market_df(
        dates=[
            "2026-08-21",  # Friday
            "2026-08-24",  # Monday
            "2026-08-25",
            "2026-08-26",
            "2026-08-27",
        ],
        closes=[
            200,
            201,
            202,
            203,
            204,
        ],
    )

    result = (
        prediction_evaluator
        .get_evaluation_dates(
            spy_df=spy,
            created_at=datetime(
                2026,
                8,
                21,
                15,
                0,
            ),
            forecast_horizon=4,
        )
    )

    assert result is not None

    entry_date, exit_date = result

    assert entry_date == pd.Timestamp(
        "2026-08-21"
    )

    assert exit_date == pd.Timestamp(
        "2026-08-27"
    )


def test_us_holiday_is_not_counted_as_session():
    # 2026-09-07 = Labor Day.
    # It is intentionally absent from SPY sessions.
    spy = make_market_df(
        dates=[
            "2026-09-04",
            "2026-09-08",
            "2026-09-09",
            "2026-09-10",
            "2026-09-11",
        ],
        closes=[
            200,
            201,
            202,
            203,
            204,
        ],
    )

    result = (
        prediction_evaluator
        .get_evaluation_dates(
            spy_df=spy,
            created_at=datetime(
                2026,
                9,
                4,
                15,
                0,
            ),
            forecast_horizon=1,
        )
    )

    assert result is not None

    _, exit_date = result

    assert exit_date == pd.Timestamp(
        "2026-09-08"
    )


def test_missing_stock_price_returns_error(
    monkeypatch,
    spy_df,
):
    prediction = make_prediction()

    stock = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
        ],
        closes=[
            100,
            101,
            102,
            103,
        ],
    )

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy_df

        return stock

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert result["evaluated"] == 0
    assert result["errors"]

    assert (
        "No MSFT price"
        in result["errors"][0]["error"]
    )


@pytest.mark.parametrize(
    (
        "direction",
        "start_price",
        "end_price",
        "expected",
    ),
    [
        (
            "Bullish",
            100.0,
            110.0,
            True,
        ),
        (
            "Bullish",
            100.0,
            90.0,
            False,
        ),
        (
            "Bearish",
            100.0,
            90.0,
            True,
        ),
        (
            "Bearish",
            100.0,
            110.0,
            False,
        ),
    ],
)
def test_prediction_direction_correctness(
    direction,
    start_price,
    end_price,
    expected,
):
    result = (
        prediction_evaluator
        .is_prediction_correct(
            predicted_direction=direction,
            start_price=start_price,
            end_price=end_price,
        )
    )

    assert result is expected


def test_bearish_short_return(
    monkeypatch,
    spy_df,
):
    prediction = make_prediction(
        predicted_direction="Bearish",
        price_at_prediction=100.0,
        spy_entry_price=200.0,
    )

    stock = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
        ],
        closes=[
            100,
            99,
            98,
            97,
            96,
        ],
    )

    saved = {}

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy_df

        return stock

    def fake_update(
        **kwargs,
    ):
        saved.update(kwargs)
        return True

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "update_prediction_result",
        fake_update,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert result["evaluated"] == 1

    assert saved["prediction_correct"] is True
    assert saved["actual_direction"] == "Bearish"

    assert saved["stock_return"] == pytest.approx(
        -0.04,
        abs=1e-6,
    )

    assert saved["short_return"] == pytest.approx(
        0.04,
        abs=1e-6,
    )


def test_spy_and_stock_use_same_exit_date(
    monkeypatch,
    spy_df,
    stock_df,
):
    prediction = make_prediction()

    saved = {}

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy_df

        return stock_df

    def fake_update(
        **kwargs,
    ):
        saved.update(kwargs)
        return True

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "update_prediction_result",
        fake_update,
    )

    prediction_evaluator.evaluate_pending_predictions()

    assert (
        saved["evaluation_market_date"]
        == pd.Timestamp(
            "2026-08-21"
        ).to_pydatetime()
    )

    assert saved["price_after_horizon"] == 104.0
    assert saved["spy_exit_price"] == 204.0


def test_horizon_is_number_of_trading_sessions():
    spy = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
            "2026-08-24",
        ],
        closes=[
            200,
            201,
            202,
            203,
            204,
            205,
        ],
    )

    result = (
        prediction_evaluator
        .get_evaluation_dates(
            spy_df=spy,
            created_at=datetime(
                2026,
                8,
                17,
                15,
                0,
            ),
            forecast_horizon=4,
        )
    )

    assert result is not None

    _, exit_date = result

    assert exit_date == pd.Timestamp(
        "2026-08-21"
    )


def test_second_evaluation_does_not_duplicate(
    monkeypatch,
    spy_df,
    stock_df,
):
    prediction = make_prediction()

    calls = []

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy_df

        return stock_df

    def fake_update(
        **kwargs,
    ):
        calls.append(kwargs)

        # Simulates repository idempotence:
        # already evaluated.
        return False

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "update_prediction_result",
        fake_update,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert len(calls) == 1
    assert result["evaluated"] == 0
    assert result["skipped"] == 1

def test_legacy_prediction_reconstructs_spy_entry_price(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            17,
            15,
            0,
        ),
        forecast_horizon=4,
        predicted_direction="Bullish",
        price_at_prediction=100.0,
        spy_entry_price=None,
    )

    spy = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
        ],
        closes=[
            200.0,
            201.0,
            202.0,
            203.0,
            204.0,
        ],
    )

    stock = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
        ],
        closes=[
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
        ],
    )

    saved = {}

    def fake_fetch(
        ticker,
        period,
        interval,
    ):
        if ticker == "SPY":
            return spy

        return stock

    def fake_update(
        **kwargs,
    ):
        saved.update(kwargs)
        return True

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        fake_fetch,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "update_prediction_result",
        fake_update,
    )

    result = (
        prediction_evaluator
        .evaluate_pending_predictions()
    )

    assert result["evaluated"] == 1
    assert result["errors"] == []

    assert saved["spy_return"] == pytest.approx(
        0.02,
        abs=1e-6,
    )

    assert saved["alpha"] == pytest.approx(
        0.02,
        abs=1e-6,
    )

    assert "spy_entry_price" not in saved


def test_pending_evaluation_not_due(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            24,
            15,
            0,
        ),
        forecast_horizon=4,
    )

    spy = make_market_df(
        dates=[
            "2026-08-24",
            "2026-08-25",
        ],
        closes=[
            200.0,
            201.0,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert result["pending_predictions"] == 1
    assert result["not_due_predictions"] == 1
    assert result["due_predictions"] == 0
    assert result["overdue_predictions"] == 0


def test_pending_evaluation_due(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            17,
            15,
            0,
        ),
        forecast_horizon=4,
    )

    spy = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
        ],
        closes=[
            200,
            201,
            202,
            203,
            204,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert result["pending_predictions"] == 1
    assert result["not_due_predictions"] == 0
    assert result["due_predictions"] == 1
    assert result["overdue_predictions"] == 0

    assert result["latest_market_date"] == (
        "2026-08-21"
    )


def test_pending_evaluation_overdue(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            17,
            15,
            0,
        ),
        forecast_horizon=4,
    )

    spy = make_market_df(
        dates=[
            "2026-08-17",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
            "2026-08-24",
        ],
        closes=[
            200,
            201,
            202,
            203,
            204,
            205,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert result["pending_predictions"] == 1
    assert result["not_due_predictions"] == 0
    assert result["due_predictions"] == 0
    assert result["overdue_predictions"] == 1

    assert result["latest_market_date"] == (
        "2026-08-24"
    )


def test_pending_evaluation_empty(
    monkeypatch,
):
    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [],
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert result == {
        "pending_predictions": 0,
        "not_due_predictions": 0,
        "due_predictions": 0,
        "overdue_predictions": 0,
        "missing_spy_entry_price": 0,
        "errors": [],
    }

def test_current_market_session_is_ignored_before_evaluation_time():
    df = make_market_df(
        dates=[
            "2026-08-26",
            "2026-08-27",
        ],
        closes=[
            200.0,
            201.0,
        ],
    )

    prepared = (
        prediction_evaluator
        .prepare_market_dataframe(df)
    )

    now = datetime(
        2026,
        8,
        27,
        10,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    result = (
        prediction_evaluator
        .keep_completed_market_sessions(
            prepared,
            now=now,
        )
    )

    assert len(result) == 1

    assert (
        result.iloc[-1]["Date"]
        .normalize()
        == pd.Timestamp(
            "2026-08-26"
        )
    )

def test_current_market_session_is_available_after_evaluation_time():
    df = make_market_df(
        dates=[
            "2026-08-26",
            "2026-08-27",
        ],
        closes=[
            200.0,
            201.0,
        ],
    )

    prepared = (
        prediction_evaluator
        .prepare_market_dataframe(df)
    )

    now = datetime(
        2026,
        8,
        27,
        18,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    result = (
        prediction_evaluator
        .keep_completed_market_sessions(
            prepared,
            now=now,
        )
    )

    assert len(result) == 2

def test_bullish_strategy_return():
    result = (
        prediction_evaluator
        .calculate_strategy_return(
            predicted_direction="Bullish",
            stock_return=0.05,
        )
    )

    assert result == 0.05


def test_bearish_strategy_return():
    result = (
        prediction_evaluator
        .calculate_strategy_return(
            predicted_direction="Bearish",
            stock_return=-0.05,
        )
    )

    assert result == 0.05


def test_neutral_strategy_return():
    result = (
        prediction_evaluator
        .calculate_strategy_return(
            predicted_direction="Neutral",
            stock_return=0.05,
        )
    )

    assert result == 0.0

def test_pending_evaluation_spy_entry_price_present(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            30,
            15,
            0,
        ),
        forecast_horizon=4,
        spy_entry_price=769.35,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    spy = make_market_df(
        dates=[
            "2026-08-28",
        ],
        closes=[
            769.35,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert (
        result["missing_spy_entry_price"]
        == 0
    )


def test_pending_evaluation_missing_spy_entry_price(
    monkeypatch,
):
    prediction = make_prediction(
        created_at=datetime(
            2026,
            8,
            30,
            15,
            0,
        ),
        forecast_horizon=4,
        spy_entry_price=None,
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "get_pending_predictions",
        lambda: [prediction],
    )

    spy = make_market_df(
        dates=[
            "2026-08-28",
        ],
        closes=[
            769.35,
        ],
    )

    monkeypatch.setattr(
        prediction_evaluator,
        "fetch_market_data",
        lambda ticker, period, interval: spy,
    )

    result = (
        prediction_evaluator
        .get_pending_evaluation_stats()
    )

    assert (
        result["missing_spy_entry_price"]
        == 1
    )

def test_scheduled_evaluation_dates():
    created_at = datetime(
        2026,
        8,
        31,
        14,
        30,
    )

    expected_dates = {
        4: "2026-09-04",
        7: "2026-09-10",
        15: "2026-09-22",
        30: "2026-10-13",
    }

    for horizon, expected_date in expected_dates.items():
        result = get_scheduled_evaluation_date(
            created_at=created_at,
            forecast_horizon=horizon,
        )

        assert (
            result.date().isoformat()
            == expected_date
        )


def test_scheduled_evaluation_date_invalid_horizon():
    result = get_scheduled_evaluation_date(
        created_at=datetime(
            2026,
            8,
            31,
        ),
        forecast_horizon=0,
    )

    assert result is None

def test_next_prospective_evaluation():
    predictions = []

    directions = [
        "Bearish",
        "Neutral",
        "Neutral",
        "Bearish",
        "Neutral",
        "Bearish",
        "Bearish",
    ]

    for index, direction in enumerate(directions):
        prediction = SimpleNamespace(
            id=index + 1,
            created_at=datetime(
                2026,
                8,
                31,
                14,
                30,
            ),
            forecast_horizon=4,
            predicted_direction=direction,
        )

        predictions.append(prediction)

    # Later evaluations must not affect
    # the first scheduled evaluation.
    predictions.append(
        SimpleNamespace(
            id=8,
            created_at=datetime(
                2026,
                8,
                31,
                14,
                30,
            ),
            forecast_horizon=7,
            predicted_direction="Bullish",
        )
    )

    result = get_next_prospective_evaluation(
        predictions
    )

    assert result == {
        "date": "2026-09-04",
        "predictions": 7,
        "directional": 4,
    }
