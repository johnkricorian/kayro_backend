from fastapi import APIRouter

from app.services.finbert import finbert_score
from app.services.news import fetch_news
from app.services.sentiment import analyze_news_sentiment
from app.services.market import fetch_market_data
from app.services.technical import compute_technical_analysis
from app.services.ml import train_and_predict

router = APIRouter(
    prefix="/test",
    tags=["Tests"]
)


@router.get("/finbert")
def test_finbert():

    text = "NVIDIA reported record AI revenue and strong guidance."

    score, sentiment = finbert_score(text)

    return {
        "text": text,
        "score": round(score, 4),
        "sentiment": sentiment
    }

@router.get("/news/{ticker}")
def test_news(ticker: str):
    articles = fetch_news(ticker)

    return {
        "ticker": ticker.upper(),
        "count": len(articles),
        "articles": articles[:5]
    }

@router.get("/sentiment/{ticker}")
def test_sentiment(ticker: str):
    return analyze_news_sentiment(ticker)

@router.get("/market/{ticker}")
def test_market(ticker: str):
    df = fetch_market_data(ticker)
    return {
        "ticker": ticker.upper(),
        "rows": len(df),
        "from": str(df.index[0]),
        "to": str(df.index[-1]),
        "last_close": round(float(df["Close"].iloc[-1]), 2),
        "last_volume": int(df["Volume"].iloc[-1]),
        "columns": list(df.columns)
    }

@router.get("/technical/{ticker}")
def test_technical(ticker: str):
    df = fetch_market_data(ticker)
    return {
        "ticker": ticker.upper(),
        "technical": compute_technical_analysis(df)
    }

@router.get("/ml/{ticker}")
def test_ml(ticker: str, forecast_horizon: int = 4):
    return train_and_predict(ticker, forecast_horizon)
