import pandas as pd
import yfinance as yf

from app.services.market_cache import get, set

def fetch_market_data(
    ticker: str,
    period: str = "5y",
    interval: str = "1d"
) -> pd.DataFrame:

    cache_key = f"{ticker}_{period}_{interval}"

    cached = get(cache_key)

    if cached is not None:
        print(f"⚡ Cache hit {ticker}")
        return cached.copy()

    print(f"⬇️ Download {ticker}")

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"No market data for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    set(cache_key, df)

    return df.copy()
