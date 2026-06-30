import pandas as pd

from app.services.scoring import build_stock_score
from app.services.sector_loader import get_sector_stocks


def scan_sector(sector: str, limit: int = 20) -> list[dict]:
    stocks = get_sector_stocks(sector)

    results = []

    for stock in stocks:
        ticker = stock["ticker"]

        try:
            score = build_stock_score(ticker)

            results.append({
                "ticker": ticker,
                "company_name": stock["company_name"],
                "score": score.get("final_score", 0),
                "signal": score.get("signal", "unknown"),
                "news_score": score.get("alpha_vantage_news", 0),
                "finbert_score": score.get("finbert_news", 0),
                "technical_score": score.get("technical_score", 0),
                "price_volume_score": score.get("price_volume", 0),
                "media_buzz_score": score.get("media_buzz", 0),
                "reasons": score.get("reasons", []),
                "market_pulse": score.get("market_pulse", {}),
                "top_articles": score.get("top_articles", [])
            })

        except Exception as error:
            print(f"❌ Error on {ticker}: {error}")

    if not results:
        return []

    return (
        pd.DataFrame(results)
        .sort_values("score", ascending=False)
        .head(limit)
        .to_dict(orient="records")
    )
