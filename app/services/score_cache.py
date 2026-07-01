from datetime import datetime, timedelta

_CACHE: dict[str, tuple[datetime, dict]] = {}

TTL = timedelta(minutes=10)


def make_key(
    ticker: str,
    forecast_horizon: int
) -> str:
    return f"{ticker.upper()}_{forecast_horizon}"


def get(
    ticker: str,
    forecast_horizon: int
) -> dict | None:
    key = make_key(ticker, forecast_horizon)

    item = _CACHE.get(key)

    if item is None:
        return None

    expires_at, value = item

    if datetime.now() > expires_at:
        del _CACHE[key]
        return None

    return value


def set(
    ticker: str,
    forecast_horizon: int,
    value: dict
):
    key = make_key(ticker, forecast_horizon)

    _CACHE[key] = (
        datetime.now() + TTL,
        value
    )


def clear():
    _CACHE.clear()
