import json
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "training_stocks.json"
)


def load_training_stocks() -> list[str]:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)["stocks"]
