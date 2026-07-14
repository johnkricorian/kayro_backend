import os
import requests
import pandas as pd
import yfinance as yf
import os

from ta.momentum import RSIIndicator
from ta.trend import MACD
from app.services.finbert import finbert_score
from threading import Lock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

def clamp(value, min_value=-1, max_value=1):
    return max(min(float(value), max_value), min_value)


def classify(score):
    if score >= 0.35:
        return "Très haussier"
    elif score >= 0.15:
        return "Haussier"
    elif score > -0.15:
        return "Neutre"
    elif score > -0.35:
        return "Baissier"
    return "Très baissier"


_ALPHA_LOCK = Lock()
_LAST_ALPHA_CALL = 0.0

MIN_CALL_INTERVAL_SECONDS = float(
    os.getenv("ALPHA_VANTAGE_MIN_INTERVAL_SECONDS", "3")
)

_retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    status=3,
    backoff_factor=2,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504,
    ],
    allowed_methods=["GET"],
    raise_on_status=False,
)

_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=_retry_strategy,
        pool_connections=4,
        pool_maxsize=4,
    ),
)

def get_news_scores(ticker: str):
    global _LAST_ALPHA_CALL
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not ALPHA_VANTAGE_API_KEY:
        return 0.0, 0.0, 0.0, []

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker.upper(),
        "apikey": api_key,
    }

    try:
        # Évite que plusieurs threads frappent Alpha Vantage simultanément.
        with _ALPHA_LOCK:
            elapsed = time.monotonic() - _LAST_ALPHA_CALL
            wait_time = MIN_CALL_INTERVAL_SECONDS - elapsed

            if wait_time > 0:
                time.sleep(wait_time)

            response = _session.get(
                url,
                params=params,
                timeout=(10, 30),
            )

            _LAST_ALPHA_CALL = time.monotonic()

        response.raise_for_status()

        data = response.json()

        if "Note" in data:
            print(
                f"⚠️ Alpha Vantage rate limit for {ticker}: "
                f"{data['Note']}"
            )
            return 0.0, 0.0, 0.0, []

        if "Information" in data:
            print(
                f"⚠️ Alpha Vantage information for {ticker}: "
                f"{data['Information']}"
            )
            return 0.0, 0.0, 0.0, []

        if "Error Message" in data:
            print(
                f"⚠️ Alpha Vantage error for {ticker}: "
                f"{data['Error Message']}"
            )
            return 0.0, 0.0, 0.0, []

        feed = data.get("feed", [])

        if not feed:
            return 0.0, 0.0, 0.0, []

        rows = []

        for article in feed:
            title = article.get("title", "")
            summary = article.get("summary", "")

            try:
                score, _ = finbert_score(
                    f"{title}. {summary}"
                )
            except Exception as error:
                print(
                    f"⚠️ FinBERT failed for {ticker}: {error}"
                )
                score = 0.0

            rows.append(
                {
                    "title": title,
                    "summary": summary,
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get(
                        "time_published",
                        "",
                    ),
                    "alpha_score": float(
                        article.get(
                            "overall_sentiment_score",
                            0,
                        )
                    ),
                    "finbert_score": float(score),
                }
            )

        df = pd.DataFrame(rows)

        if df.empty:
            return 0.0, 0.0, 0.0, []

        alpha_score = clamp(
            float(df["alpha_score"].mean())
        )

        finbert_news_score = clamp(
            float(df["finbert_score"].mean())
        )

        media_buzz_score = clamp(
            len(df) / 50
        )

        articles = (
            df.sort_values(
                "finbert_score",
                ascending=False,
            )
            .head(5)
            .to_dict("records")
        )

        return (
            alpha_score,
            finbert_news_score,
            media_buzz_score,
            articles,
        )

    except requests.exceptions.Timeout:
        print(
            f"⚠️ Alpha Vantage timeout for {ticker}"
        )

    except requests.exceptions.SSLError as error:
        print(
            f"⚠️ Alpha Vantage SSL error for {ticker}: "
            f"{error}"
        )

    except requests.exceptions.RequestException as error:
        print(
            f"⚠️ Alpha Vantage request error for {ticker}: "
            f"{error}"
        )

    except ValueError as error:
        print(
            f"⚠️ Invalid Alpha Vantage JSON for {ticker}: "
            f"{error}"
        )

    except Exception as error:
        print(
            f"⚠️ Unexpected news error for {ticker}: "
            f"{error}"
        )

    return 0.0, 0.0, 0.0, []

def get_market_data(ticker):
    df = yf.download(
        ticker,
        period="1y",
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()


def get_price_volume_score(df):
    if df.empty or len(df) < 30:
        return 0

    close = df["Close"]
    volume = df["Volume"]

    perf_5d = (close.iloc[-1] / close.iloc[-5]) - 1
    perf_20d = (close.iloc[-1] / close.iloc[-20]) - 1
    volume_ratio = volume.iloc[-1] / max(volume.tail(20).mean(), 1)

    price_score = clamp((0.6 * perf_5d + 0.4 * perf_20d) * 5)
    volume_score = clamp((volume_ratio - 1) / 2)

    return clamp(0.7 * price_score + 0.3 * volume_score)


def get_technical_score(df):
    if df.empty or len(df) < 60:
        return 0

    close = df["Close"]

    rsi = RSIIndicator(close=close, window=14).rsi()
    macd = MACD(close=close)

    latest_rsi = float(rsi.iloc[-1])
    latest_macd_diff = float(macd.macd_diff().iloc[-1])
    latest_close = float(close.iloc[-1])

    if latest_rsi < 30:
        rsi_score = 0.6
    elif latest_rsi < 45:
        rsi_score = 0.2
    elif latest_rsi <= 60:
        rsi_score = 0.1
    elif latest_rsi <= 70:
        rsi_score = 0.3
    else:
        rsi_score = -0.4

    macd_score = clamp(latest_macd_diff / max(latest_close * 0.01, 0.01))
    momentum_50d = (close.iloc[-1] / close.iloc[-50]) - 1
    momentum_score = clamp(momentum_50d * 3)

    return clamp(
        0.35 * rsi_score +
        0.35 * macd_score +
        0.30 * momentum_score
    )


def build_score_reasons(
    alpha_score,
    finbert_news_score,
    media_buzz_score,
    price_volume_score,
    technical_score
):
    reasons = []

    if technical_score > 0.35:
        reasons.append("Positive technical momentum detected")
    elif technical_score > 0.15:
        reasons.append("Technical indicators are improving")

    if price_volume_score > 0.35:
        reasons.append("Price and volume are above average")
    elif price_volume_score > 0.15:
        reasons.append("Recent price action is constructive")

    if finbert_news_score > 0.35:
        reasons.append("Financial news sentiment is strongly positive")
    elif finbert_news_score > 0.15:
        reasons.append("Financial news sentiment is favorable")

    if alpha_score > 0.25:
        reasons.append("Alpha Vantage market sentiment is positive")

    if media_buzz_score > 0.6:
        reasons.append("High media coverage detected")
    elif media_buzz_score > 0.3:
        reasons.append("Rising media attention detected")

    if not reasons:
        reasons.append("No strong positive signal detected yet")

    return reasons[:4]


def percent_from_score(score):
    return round(((clamp(score) + 1) / 2) * 100)


def market_sentiment_label(score):
    if score >= 0.35:
        return "Very Bullish"
    elif score >= 0.15:
        return "Bullish"
    elif score > -0.15:
        return "Neutral"
    elif score > -0.35:
        return "Bearish"
    return "Very Bearish"


def media_buzz_label(article_count):
    if article_count >= 40:
        return "Very high media coverage"
    elif article_count >= 20:
        return "High media coverage"
    elif article_count >= 10:
        return "Moderate media coverage"
    elif article_count > 0:
        return "Low media coverage"
    return "No major media coverage"


def trend_label(price_volume_score):
    if price_volume_score >= 0.35:
        return "Strong price and volume momentum"
    elif price_volume_score >= 0.15:
        return "Positive price and volume trend"
    elif price_volume_score > -0.15:
        return "Stable price and volume trend"
    return "Weak price and volume trend"


def technical_label(technical_score):
    if technical_score >= 0.35:
        return "Strong technical setup"
    elif technical_score >= 0.15:
        return "Improving technical setup"
    elif technical_score > -0.15:
        return "Neutral technical setup"
    return "Weak technical setup"


def detect_main_catalyst(articles, technical_score, price_volume_score, finbert_news_score):
    text = " ".join(
        article.get("title", "") + " " + article.get("summary", "")
        for article in articles
    ).lower()

    catalysts = [
        ("AI infrastructure demand", ["ai", "artificial intelligence", "gpu", "data center"]),
        ("Semiconductor cycle recovery", ["chip", "semiconductor", "foundry"]),
        ("Earnings momentum", ["earnings", "revenue", "profit", "guidance"]),
        ("Cloud growth", ["cloud", "aws", "azure", "google cloud"]),
        ("Cybersecurity demand", ["cybersecurity", "security", "breach"]),
        ("Crypto market momentum", ["bitcoin", "crypto", "ethereum"]),
        ("Energy price momentum", ["oil", "gas", "energy"]),
        ("Defense spending growth", ["defense", "military", "contract"]),
        ("EV and autonomous driving demand", ["ev", "electric vehicle", "autonomous"]),
        ("Positive media coverage", ["upgrade", "bullish", "buy rating"])
    ]

    for catalyst, keywords in catalysts:
        if any(keyword in text for keyword in keywords):
            return catalyst

    if finbert_news_score > 0.25:
        return "Positive financial news sentiment"

    if price_volume_score > 0.25:
        return "Price and volume momentum"

    if technical_score > 0.25:
        return "Technical momentum"

    return "Market activity remains neutral"


def build_ai_explanation(
    ticker,
    final_score,
    finbert_news_score,
    media_buzz_score,
    price_volume_score,
    technical_score,
    main_catalyst
):
    return (
        f"{ticker} currently shows a {market_sentiment_label(final_score).lower()} setup. "
        f"Kayro detected {technical_label(technical_score).lower()}, "
        f"{trend_label(price_volume_score).lower()}, and "
        f"{media_buzz_label(round(media_buzz_score * 50)).lower()}. "
        f"The main catalyst appears to be {main_catalyst.lower()}."
    )


def build_market_pulse(
    ticker,
    final_score,
    alpha_score,
    finbert_news_score,
    media_buzz_score,
    price_volume_score,
    technical_score,
    articles
):
    article_count = round(media_buzz_score * 50)

    main_catalyst = detect_main_catalyst(
        articles=articles,
        technical_score=technical_score,
        price_volume_score=price_volume_score,
        finbert_news_score=finbert_news_score
    )

    popularity_score = min(
        100,
        round(
            article_count * 1.5 +
            max(price_volume_score, 0) * 35 +
            max(technical_score, 0) * 25 +
            max(finbert_news_score, 0) * 30
        )
    )

    return {
        "sentiment_label": market_sentiment_label(final_score),
        "positive_sentiment_percent": percent_from_score(finbert_news_score),
        "media_buzz_label": media_buzz_label(article_count),
        "news_count": article_count,
        "trend_label": trend_label(price_volume_score),
        "trend_percent": round(max(price_volume_score, 0) * 100),
        "technical_label": technical_label(technical_score),
        "technical_percent": round(max(technical_score, 0) * 100),
        "popularity_score": popularity_score,
        "main_catalyst": main_catalyst,
        "ai_explanation": build_ai_explanation(
            ticker=ticker,
            final_score=final_score,
            finbert_news_score=finbert_news_score,
            media_buzz_score=media_buzz_score,
            price_volume_score=price_volume_score,
            technical_score=technical_score,
            main_catalyst=main_catalyst
        )
    }

def build_stock_score(ticker: str) -> dict:
    ticker = ticker.upper()

    try:
        (
            alpha_score,
            finbert_news_score,
            media_buzz_score,
            articles,
        ) = get_news_scores(ticker)

    except Exception as error:
        logger.warning(
            "News unavailable for %s: %s",
            ticker,
            error,
        )

        alpha_score = 0.0
        finbert_news_score = 0.0
        media_buzz_score = 0.0
        articles = []

    market_df = get_market_data(ticker)
    price_volume_score = get_price_volume_score(market_df)
    technical_score = get_technical_score(market_df)

    final_score = clamp(
        alpha_score * 0.30 +
        finbert_news_score * 0.30 +
        media_buzz_score * 0.20 +
        price_volume_score * 0.10 +
        technical_score * 0.10
    )

    reasons = build_score_reasons(
        alpha_score=alpha_score,
        finbert_news_score=finbert_news_score,
        media_buzz_score=media_buzz_score,
        price_volume_score=price_volume_score,
        technical_score=technical_score
    )

    return {
        "ticker": ticker,
        "company_name": ticker,
        "final_score": round(final_score, 4),
        "signal": classify(final_score),
        "alpha_vantage_news": round(alpha_score, 4),
        "finbert_news": round(finbert_news_score, 4),
        "technical_score": round(technical_score, 4),
        "price_volume": round(price_volume_score, 4),
        "media_buzz": round(media_buzz_score, 4),
        "reasons": reasons,
        "market_pulse": build_market_pulse(
            ticker=ticker,
            final_score=final_score,
            alpha_score=alpha_score,
            finbert_news_score=finbert_news_score,
            media_buzz_score=media_buzz_score,
            price_volume_score=price_volume_score,
            technical_score=technical_score,
            articles=articles
        ),
        "top_articles": articles
    }
