import json
from pathlib import Path
import pandas as pd

from app.scoring import build_stock_score

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "sectors.json"
)

def load_sectors():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
