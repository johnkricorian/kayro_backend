from app.database.portfolio_repository import get_positions
from app.services.market import fetch_market_data
from app.services.score_engine import build_stock_score
from app.services.sector_loader import load_sectors

def analyze_portfolio() -> dict:

    positions = get_positions()

    if not positions:
        return {
            "portfolio_value": 0,
            "portfolio_score": 0,
            "positions": []
        }

    analyzed = []

    portfolio_value = 0

    for position in positions:

        current_price = get_current_price(position.ticker)

        market_value = current_price * position.quantity

        portfolio_value += market_value

        performance = (
            (current_price - position.average_price)
            / position.average_price
        ) * 100

        score = build_stock_score(position.ticker)

        analyzed.append({
            "ticker": position.ticker,
            "quantity": position.quantity,
            "average_price": position.average_price,
            "current_price": round(current_price, 2),
            "market_value": round(market_value, 2),
            "performance": round(performance, 2),
            "kayro_score": score["kayro_score"],
            "recommendation": score["recommendation"]
        })

    for position in analyzed:

        position["weight"] = round(
            position["market_value"] /
            portfolio_value *
            100,
            2
        )

    analyzed.sort(
        key=lambda x: x["market_value"],
        reverse=True
    )
    portfolio_score = compute_portfolio_score(analyzed)
    sector_exposure = compute_sector_exposure(analyzed)
    diversification = compute_diversification_score(analyzed, sector_exposure)
    risk = compute_risk_score(diversification)
    best = best_position(analyzed)
    worst = worst_position(analyzed)

    return {
        "portfolio_value": round(portfolio_value, 2),
        "portfolio_score": portfolio_score,
        "positions": analyzed,
        "best_position": best,
        "worst_position": worst,
        "sector_exposure": sector_exposure,
        "diversification": diversification,
        "risk": risk,
        "insights": build_insights(
            positions=analyzed,
            portfolio_score=portfolio_score
        ),

        "advisor_summary": build_advisor_summary(
            portfolio_score=portfolio_score,
            diversification=diversification,
            risk=risk,
            best=best,
            worst=worst
        )
    }


def get_current_price(
    ticker: str
) -> float:

    df = fetch_market_data(
        ticker=ticker,
        period="5d",
        interval="1d"
    )

    return float(
        df["Close"].iloc[-1]
    )


def compute_portfolio_score(
    positions: list[dict]
) -> int:

    if not positions:
        return 0

    total_weight = sum(
        p["weight"] for p in positions
    )

    score = sum(
        p["kayro_score"] * p["weight"]
        for p in positions
    ) / total_weight

    return round(score)


def best_position(
    positions: list[dict]
):

    return max(
        positions,
        key=lambda x: x["kayro_score"]
    )["ticker"]


def worst_position(
    positions: list[dict]
):

    return min(
        positions,
        key=lambda x: x["kayro_score"]
    )["ticker"]

def build_insights(
    positions: list[dict],
    portfolio_score: int
) -> list[str]:

    insights = []

    if not positions:
        return ["No portfolio positions found."]

    top_weight = max(positions, key=lambda x: x["weight"])

    if top_weight["weight"] > 50:
        insights.append(
            f"{top_weight['ticker']} represents {top_weight['weight']}% of your portfolio. "
            "This creates a high concentration risk."
        )
    elif top_weight["weight"] > 30:
        insights.append(
            f"{top_weight['ticker']} is your largest position at {top_weight['weight']}%. "
            "Your portfolio is moderately concentrated."
        )

    if len(positions) < 5:
        insights.append(
            "Your portfolio has fewer than 5 positions. Diversification is limited."
        )

    strong_positions = [
        p for p in positions
        if p["kayro_score"] >= 75
    ]

    weak_positions = [
        p for p in positions
        if p["kayro_score"] < 50
    ]

    if strong_positions:
        best = max(strong_positions, key=lambda x: x["kayro_score"])
        insights.append(
            f"{best['ticker']} is your strongest position with a Kayro Score of {best['kayro_score']}."
        )

    if weak_positions:
        worst = min(weak_positions, key=lambda x: x["kayro_score"])
        insights.append(
            f"{worst['ticker']} is your weakest position with a Kayro Score of {worst['kayro_score']}."
        )

    if portfolio_score >= 80:
        insights.append(
            "Your portfolio has a strong overall Kayro Score."
        )
    elif portfolio_score >= 60:
        insights.append(
            "Your portfolio is balanced but still has room for optimization."
        )
    else:
        insights.append(
            "Your portfolio score is weak. Consider reducing exposure to low-scoring positions."
        )

    return insights

def find_sector_for_ticker(ticker: str) -> str:
    sectors = load_sectors()
    ticker = ticker.upper()

    for sector, stocks in sectors.items():
        for stock in stocks:
            if stock["ticker"].upper() == ticker:
                return sector

    return "other"


def compute_sector_exposure(
    positions: list[dict]
) -> list[dict]:

    exposure = {}

    for position in positions:
        sector = find_sector_for_ticker(position["ticker"])

        exposure[sector] = exposure.get(sector, 0) + position["weight"]

    return [
        {
            "sector": sector,
            "weight": round(weight, 2)
        }
        for sector, weight in sorted(
            exposure.items(),
            key=lambda item: item[1],
            reverse=True
        )
    ]

def compute_diversification_score(
    positions: list[dict],
    sector_exposure: list[dict]
) -> dict:
    score = 0

    max_position_weight = max(
        position["weight"] for position in positions
    ) if positions else 0

    max_sector_weight = max(
        sector["weight"] for sector in sector_exposure
    ) if sector_exposure else 0

    if len(positions) >= 10:
        score += 3
    elif len(positions) >= 5:
        score += 2
    elif len(positions) >= 3:
        score += 1

    if len(sector_exposure) >= 5:
        score += 3
    elif len(sector_exposure) >= 3:
        score += 2
    elif len(sector_exposure) >= 2:
        score += 1

    if max_position_weight <= 30:
        score += 2
    elif max_position_weight <= 50:
        score += 1

    if max_sector_weight <= 40:
        score += 2
    elif max_sector_weight <= 60:
        score += 1

    return {
        "score": score,
        "label": diversification_label(score),
        "max_position_weight": round(max_position_weight, 2),
        "max_sector_weight": round(max_sector_weight, 2),
        "positions_count": len(positions),
        "sectors_count": len(sector_exposure)
    }


def diversification_label(score: int) -> str:
    if score >= 9:
        return "Excellent"
    if score >= 7:
        return "Good"
    if score >= 4:
        return "Fair"
    return "Poor"


def compute_risk_score(
    diversification: dict
) -> dict:
    risk_score = 100

    risk_score -= diversification["max_position_weight"] * 0.7
    risk_score -= diversification["max_sector_weight"] * 0.4

    if diversification["positions_count"] < 5:
        risk_score -= 15

    if diversification["sectors_count"] < 3:
        risk_score -= 15

    risk_score = max(0, min(100, round(risk_score)))

    return {
        "score": risk_score,
        "label": risk_label(risk_score)
    }


def risk_label(score: int) -> str:
    if score >= 75:
        return "Low"
    if score >= 50:
        return "Medium"
    return "High"


def build_advisor_summary(
    portfolio_score: int,
    diversification: dict,
    risk: dict,
    best: str,
    worst: str
) -> str:
    return (
        f"Your portfolio has a Kayro Score of {portfolio_score}/100. "
        f"Diversification is {diversification['label'].lower()} "
        f"with {diversification['positions_count']} positions across "
        f"{diversification['sectors_count']} sectors. "
        f"Risk is currently {risk['label'].lower()}. "
        f"{best} is your strongest position, while {worst} is the weakest."
    )
