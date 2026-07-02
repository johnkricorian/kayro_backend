from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.portfolio_repository import (
    add_position,
    get_positions,
    update_position,
    delete_position
)


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


class PortfolioPositionRequest(BaseModel):
    ticker: str
    quantity: float
    average_price: float


@router.get("")
def list_portfolio():
    rows = get_positions()

    return [
        {
            "id": row.id,
            "ticker": row.ticker,
            "quantity": row.quantity,
            "average_price": row.average_price,
            "created_at": row.created_at
        }
        for row in rows
    ]


@router.post("")
def create_position(payload: PortfolioPositionRequest):
    position = add_position(
        ticker=payload.ticker,
        quantity=payload.quantity,
        average_price=payload.average_price
    )

    return {
        "id": position.id,
        "ticker": position.ticker,
        "quantity": position.quantity,
        "average_price": position.average_price,
        "created_at": position.created_at
    }


@router.put("/{ticker}")
def edit_position(
    ticker: str,
    payload: PortfolioPositionRequest
):
    position = update_position(
        ticker=ticker,
        quantity=payload.quantity,
        average_price=payload.average_price
    )

    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")

    return {
        "id": position.id,
        "ticker": position.ticker,
        "quantity": position.quantity,
        "average_price": position.average_price,
        "created_at": position.created_at
    }


@router.delete("/{ticker}")
def remove_position(ticker: str):
    deleted = delete_position(ticker)

    if not deleted:
        raise HTTPException(status_code=404, detail="Position not found")

    return {"deleted": True}
