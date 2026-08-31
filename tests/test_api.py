from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_get_portfolio():
    response = client.get("/portfolio")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_stats():
    response = client.get("/stats")

    assert response.status_code == 200

    data = response.json()

    assert "total_predictions" in data
    assert "accuracy" in data
    assert "pending_predictions" in data


def test_get_leaderboard():
    response = client.get("/leaderboard?limit=10")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_predictions():
    response = client.get("/predictions?limit=10")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_portfolio_crud():
    payload = {
        "ticker": "TESTAPI",
        "quantity": 3,
        "average_price": 100
    }

    response = client.post("/portfolio", json=payload)
    assert response.status_code == 200
    assert response.json()["ticker"] == "TESTAPI"

    response = client.get("/portfolio")
    assert response.status_code == 200

    response = client.put(
        "/portfolio/TESTAPI",
        json={
            "ticker": "TESTAPI",
            "quantity": 5,
            "average_price": 120
        }
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 5

    response = client.delete("/portfolio/TESTAPI")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

def test_performance_endpoint():
    response = client.get(
        "/evaluation/performance"
    )

    assert response.status_code == 200

    data = response.json()

    assert "performance" in data

    performance = data["performance"]

    assert (
        performance[
            "validation_start_date"
        ]
        == "2026-08-31"
    )

    assert (
        "directional_evaluated"
        in performance
    )

    assert "accuracy" in performance
    assert "progress" in performance
    assert "portfolio" in performance
    assert "benchmark" in performance

    assert (
        "excess_return_vs_spy"
        in performance["benchmark"]
    )
