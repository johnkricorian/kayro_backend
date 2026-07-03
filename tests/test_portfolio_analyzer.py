from app.services.portfolio_analyzer import (
    compute_diversification_score,
    compute_risk_score,
    compute_portfolio_score,
    diversification_label,
    risk_label,
)


def test_compute_portfolio_score():
    positions = [
        {"kayro_score": 80, "weight": 60},
        {"kayro_score": 60, "weight": 40},
    ]

    assert compute_portfolio_score(positions) == 72


def test_diversification_score_poor():
    positions = [
        {"ticker": "NVDA", "weight": 70},
        {"ticker": "AAPL", "weight": 30},
    ]

    sectors = [
        {"sector": "technology", "weight": 100}
    ]

    result = compute_diversification_score(positions, sectors)

    assert result["label"] == "Poor"
    assert result["max_position_weight"] == 70
    assert result["max_sector_weight"] == 100


def test_diversification_score_good():
    positions = [
        {"ticker": f"STOCK{i}", "weight": 10}
        for i in range(10)
    ]

    sectors = [
        {"sector": f"sector{i}", "weight": 20}
        for i in range(5)
    ]

    result = compute_diversification_score(positions, sectors)

    assert result["score"] == 10
    assert result["label"] == "Excellent"


def test_risk_score_high():
    diversification = {
        "max_position_weight": 70,
        "max_sector_weight": 100,
        "positions_count": 2,
        "sectors_count": 1,
    }

    result = compute_risk_score(diversification)

    assert result["label"] == "High"


def test_labels():
    assert diversification_label(9) == "Excellent"
    assert diversification_label(7) == "Good"
    assert diversification_label(4) == "Fair"
    assert diversification_label(3) == "Poor"

    assert risk_label(80) == "Low"
    assert risk_label(60) == "Medium"
    assert risk_label(30) == "High"
