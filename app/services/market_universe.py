from app.services.fmp import screen_stocks


def get_market_universe(
    *,
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    exchange: str | None = None,
    limit: int = 500
) -> list[dict]:

    stocks = screen_stocks(
        sector=sector,
        industry=industry,
        country=country,
        exchange=exchange,
        market_cap_more_than=300_000_000,
        price_more_than=2,
        limit=limit
    )

    return [
        {
            "ticker": stock.get("symbol"),
            "company": stock.get("companyName"),
            "sector": stock.get("sector"),
            "industry": stock.get("industry"),
            "country": stock.get("country"),
            "exchange": (
                stock.get("exchangeShortName")
                or stock.get("exchange")
            ),
            "market_cap": stock.get("marketCap"),
            "price": stock.get("price"),
            "volume": stock.get("volume"),
        }
        for stock in stocks
        if stock.get("symbol")
    ]
