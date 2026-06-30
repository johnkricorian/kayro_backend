import pandas as pd
import yfinance as yf


def fetch_market_data(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Download historical market data.
    """

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(f"No market data found for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()
