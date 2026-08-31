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
