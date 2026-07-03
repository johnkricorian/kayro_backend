from app.database.portfolio_repository import (
    add_position,
    get_position,
    get_positions,
    update_position,
    delete_position,
)


def test_add_position():
    delete_position("TEST")

    position = add_position(
        ticker="TEST",
        quantity=10,
        average_price=100
    )

    assert position.ticker == "TEST"
    assert position.quantity == 10
    assert position.average_price == 100

    delete_position("TEST")


def test_get_position():
    delete_position("TEST")

    add_position("TEST", 5, 120)

    position = get_position("TEST")

    assert position is not None
    assert position.ticker == "TEST"
    assert position.quantity == 5

    delete_position("TEST")


def test_get_positions():
    delete_position("TEST1")
    delete_position("TEST2")

    add_position("TEST1", 1, 100)
    add_position("TEST2", 2, 200)

    positions = get_positions()
    tickers = [position.ticker for position in positions]

    assert "TEST1" in tickers
    assert "TEST2" in tickers

    delete_position("TEST1")
    delete_position("TEST2")


def test_update_position():
    delete_position("TEST")

    add_position("TEST", 5, 100)

    updated = update_position(
        ticker="TEST",
        quantity=12,
        average_price=150
    )

    assert updated is not None
    assert updated.quantity == 12
    assert updated.average_price == 150

    delete_position("TEST")


def test_delete_position():
    delete_position("TEST")

    add_position("TEST", 3, 80)

    deleted = delete_position("TEST")

    assert deleted is True
    assert get_position("TEST") is None
