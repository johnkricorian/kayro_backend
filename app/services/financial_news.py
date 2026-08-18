from app.services.fmp_client import fmp_client


def get_stock_news(
    ticker: str,
    limit: int = 20
) -> list[dict]:
    ticker = ticker.upper()

    raw = fmp_client.get(
        "news/stock",
        params={
            "symbols": ticker,
            "limit": limit,
        }
    )

    if not isinstance(raw, list):
        return []

    normalized = []

    for item in raw:
        normalized.append({
            "ticker": ticker,
            "title": item.get("title"),
            "summary": (
                item.get("text")
                or item.get("summary")
                or item.get("snippet")
            ),
            "published_at": (
                item.get("publishedDate")
                or item.get("published_at")
            ),
            "source": (
                item.get("site")
                or item.get("source")
            ),
            "url": item.get("url"),
            "image_url": (
                item.get("image")
                or item.get("image_url")
            ),
            "provider": "fmp",
        })

    return normalized
