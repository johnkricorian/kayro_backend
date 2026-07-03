from pathlib import Path
from app.core.exceptions import PortfolioError
import json

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sectors.json"
)


def load_sectors() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_available_sectors() -> list[str]:
    return sorted(load_sectors().keys())


def get_sector_stocks(sector: str) -> list[dict]:
    sectors = load_sectors()

    if sector not in sectors:
        raise PortfolioError(f"Unknown sector '{sector}'")

    return sectors[sector]
