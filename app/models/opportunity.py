from pydantic import BaseModel


class Opportunity(BaseModel):
    ticker: str
    company_name: str
    sector: str
    kayro_score: int
    recommendation: str
    prediction: str
    confidence: float
    price: float
    change_percent: float
    signals: list[str]
    logo: str | None = None
    sentiment_label: str
    positive_sentiment_percent: int
    media_buzz_label: str
    news_count: int
    trend_label: str
    trend_percent: int
    technical_label: str
    technical_percent: int
    popularity_score: int
    main_catalyst: str
    ai_explanation: str
    reasons: list[str]
