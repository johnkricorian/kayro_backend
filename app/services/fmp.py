from app.services.fmp_client import fmp_client


def get_available_sectors() -> list:
    return fmp_client.get(
        "available-sectors"
    )


def get_available_industries() -> list:
    return fmp_client.get(
        "available-industries"
    )


def get_available_countries() -> list:
    return fmp_client.get(
        "available-countries"
    )


def get_company_profile(
    ticker: str
) -> list:
    return fmp_client.get(
        "profile",
        params={
            "symbol": ticker.upper()
        }
    )


def screen_stocks(
    *,
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    exchange: str | None = None,
    market_cap_more_than: int | None = None,
    price_more_than: float | None = None,
    volume_more_than: int | None = None,
    limit: int = 100
) -> list:

    params = {
        "limit": limit
    }

    if sector:
        params["sector"] = sector

    if industry:
        params["industry"] = industry

    if country:
        params["country"] = country

    if exchange:
        params["exchange"] = exchange

    if market_cap_more_than is not None:
        params["marketCapMoreThan"] = market_cap_more_than

    if price_more_than is not None:
        params["priceMoreThan"] = price_more_than

    if volume_more_than is not None:
        params["volumeMoreThan"] = volume_more_than

    return fmp_client.get(
        "company-screener",
        params=params
    )
