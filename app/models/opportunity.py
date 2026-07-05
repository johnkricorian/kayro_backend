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
