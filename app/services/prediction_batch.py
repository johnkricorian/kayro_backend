from app.services.qeyro_score import build_qeyro_score

DEFAULT_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
]

DEFAULT_HORIZONS = [
    4,
    7,
    15,
    30,
]

def generate_prediction_batch(
    tickers: list[str] | None = None,
    horizons: list[int] | None = None,
    force_refresh: bool = True,
) -> dict:
    tickers = tickers or DEFAULT_TICKERS
    horizons = horizons or DEFAULT_HORIZONS

    generated = []
    errors = []

    for ticker in tickers:
        for horizon in horizons:
            try:
                result = build_qeyro_score(
                    ticker=ticker,
                    forecast_horizon=horizon,
                    force_refresh=force_refresh,
                )

                generated.append({
                    "ticker": ticker.upper(),
                    "forecast_horizon": horizon,
                    "qeyro_score": result["qeyro_score"],
                    "recommendation": result["recommendation"],
                    "direction": result["prediction"]["direction"],
                    "probability_up": result["prediction"]["probability_up"],
                })

            except Exception as error:
                errors.append({
                    "ticker": ticker.upper(),
                    "forecast_horizon": horizon,
                    "error": str(error),
                })

    return {
        "requested": len(tickers) * len(horizons),
        "generated": len(generated),
        "errors_count": len(errors),
        "force_refresh": force_refresh,
        "predictions": generated,
        "errors": errors,
    }
