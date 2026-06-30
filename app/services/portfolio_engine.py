from app.services.sector_loader import load_sectors
from app.services.score_engine import build_stock_score


def rank_stocks(
    tickers: list[dict],
    limit: int = 20,
    forecast_horizon: int = 15
) -> list[dict]:

    results = []

    for stock in tickers:
        ticker = stock["ticker"]

        try:
            score = build_stock_score(
                ticker=ticker,
                forecast_horizon=forecast_horizon
            )

            results.append({
                "ticker": ticker,
                "company_name": stock.get("company_name", ticker),
                "kayro_score": score["kayro_score"],
                "recommendation": score["recommendation"],
                "confidence": score["confidence"],
                "signals": score["signals"][:4],
                "prediction": score["prediction"],
                "technical": score["technical"]
            })

        except Exception as error:
            print(f"❌ Portfolio ranking error on {ticker}: {error}")

    return sorted(
        results,
        key=lambda item: item["kayro_score"],
        reverse=True
    )[:limit]


def rank_all_stocks(
    limit: int = 20,
    forecast_horizon: int = 15
) -> list[dict]:

    sectors = load_sectors()

    seen = set()
    stocks = []

    for sector_stocks in sectors.values():
        for stock in sector_stocks:
            ticker = stock["ticker"]

            if ticker not in seen:
                seen.add(ticker)
                stocks.append(stock)

    return rank_stocks(
        tickers=stocks,
        limit=limit,
        forecast_horizon=forecast_horizon
    )


def rank_sector(
    sector: str,
    limit: int = 20,
    forecast_horizon: int = 15
) -> list[dict]:

    sectors = load_sectors()

    if sector not in sectors:
        raise ValueError(f"Unknown sector '{sector}'")

    return rank_stocks(
        tickers=sectors[sector],
        limit=limit,
        forecast_horizon=forecast_horizon
    )
