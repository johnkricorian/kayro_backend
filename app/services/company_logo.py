import os
from urllib.parse import quote

LOGO_DEV_API_KEY = os.getenv("LOGO_DEV_API_KEY")

def build_company_logo_url(
    ticker: str,
    *,
    size: int = 128,
) -> str | None:
    """
    Returns a public PNG URL for a stock ticker.

    The frontend can load this URL directly.
    """
    if not LOGO_DEV_API_KEY:
        return None

    normalized_ticker = ticker.strip().upper()

    if not normalized_ticker:
        return None

    encoded_ticker = quote(
        normalized_ticker,
        safe="",
    )

    return (
        f"https://img.logo.dev/ticker/{encoded_ticker}"
        f"?token={LOGO_DEV_API_KEY}"
        f"&format=png"
        f"&size={size}"
    )
