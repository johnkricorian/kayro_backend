from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models.opportunity import Opportunity
from app.services.score_engine import build_stock_score
from app.services.market import fetch_market_data
from app.services.sector_loader import load_sectors
from app.services.opportunity_presenter import OpportunityPresenter

def build_opportunity(
    ticker: str,
    sector: str,
    forecast_horizon: int
) -> Opportunity | None:
    try:
        score = build_stock_score(
            ticker=ticker,
            forecast_horizon=forecast_horizon
        )

        market = fetch_market_data(
            ticker=ticker,
            period="5d",
            interval="1d"
        )

        latest = market.iloc[-1]
        previous = market.iloc[-2]

        change_percent = (
            (latest["Close"] - previous["Close"])
            / previous["Close"]
        ) * 100

        sentiment = score["sentiment"]
        technical = score["technical"]
        prediction = score["prediction"]

        positive_sentiment = round(sentiment["finbert_score"] * 100)
        technical_percent = OpportunityPresenter.technical_percent(
            technical["technical_score"]
        )
        news_count = len(sentiment["articles"])

        return Opportunity(
            ticker=ticker,
            company_name=ticker,
            sector=sector,
            kayro_score=score["kayro_score"],
            recommendation=score["recommendation"],
            prediction=prediction["direction"],
            confidence=prediction["confidence"],
            price=round(float(latest["Close"]), 2),
            change_percent=round(float(change_percent), 2),
            signals=[
                signal["title"]
                for signal in score["signals"][:3]
            ],
            logo=None,
            sentiment_label=OpportunityPresenter.sentiment_label(
                positive_sentiment
            ),
            positive_sentiment_percent=positive_sentiment,
            media_buzz_label=OpportunityPresenter.media_buzz_label(
                sentiment["media_buzz"]
            ),
            news_count=news_count,
            trend_label=technical["trend"],
            trend_percent=round(prediction["confidence"]),
            technical_label=OpportunityPresenter.technical_label(
                technical_percent
            ),
            technical_percent=technical_percent,
            popularity_score=OpportunityPresenter.popularity_score(
                news_count=news_count,
                media_buzz=sentiment["media_buzz"]
            ),
            main_catalyst=OpportunityPresenter.main_catalyst(
                score["signals"]
            ),
            ai_explanation=OpportunityPresenter.ai_explanation(
                prediction=prediction,
                technical=technical,
                news_count=news_count
            ),
            reasons=[signal["description"] for signal in score["signals"][:3]]
        )

    except Exception as error:
        print(f"❌ Opportunity error on {ticker}: {error}")
        return None


def get_opportunities(
    sectors: list[str],
    limit: int = 20,
    forecast_horizon: int = 15
) -> list[Opportunity]:
    sector_map = load_sectors()

    selected_stocks: dict[str, dict] = {}

    for sector in sectors:
        sector_key = sector.lower()

        if sector_key not in sector_map:
            print(f"⚠️ Unknown sector ignored: {sector}")
            continue

        for stock in sector_map[sector_key]:
            ticker = stock["ticker"].upper()

            selected_stocks[ticker] = {
                "ticker": ticker,
                "sector": sector_key
            }

    stocks = list(selected_stocks.values())

    if not stocks:
        return []

    results: list[Opportunity] = []

    max_workers = min(8, len(stocks))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                build_opportunity,
                stock["ticker"],
                stock["sector"],
                forecast_horizon
            ): stock["ticker"]
            for stock in stocks
        }

        for future in as_completed(futures):
            opportunity = future.result()

            if opportunity is not None:
                results.append(opportunity)

    results.sort(
        key=lambda item: item.kayro_score,
        reverse=True
    )

    return results[:limit]
