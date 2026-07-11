from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

loaded = load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

print("ENV path:", ENV_PATH)
print("ENV loaded:", loaded)
print(
    "ALPHA_VANTAGE_API_KEY available:",
    bool(os.getenv("ALPHA_VANTAGE_API_KEY"))
)

from concurrent.futures import ThreadPoolExecutor, as_completed
from app.database.database import SessionLocal
from app.repositories.opportunity_repository import save_opportunities
from app.services.opportunity_service import build_opportunity
from app.services.sector_loader import load_sectors

import os

print("ENV file:", ROOT_DIR / ".env")
print(
    "Alpha Vantage key loaded:",
    bool(os.getenv("ALPHA_VANTAGE_API_KEY"))
)

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

FORECAST_HORIZON = 15
MAX_WORKERS = 8

def generate() -> int:
    sector_map = load_sectors()

    stocks: list[dict] = []

    for sector, sector_stocks in sector_map.items():
        for stock in sector_stocks:
            stocks.append({
                "ticker": stock["ticker"].upper(),
                "sector": sector
            })

    print(f"🚀 Generating opportunities for {len(stocks)} stocks...")

    results: list[dict] = []

    with ThreadPoolExecutor(
        max_workers=min(MAX_WORKERS, len(stocks))
    ) as executor:
        futures = {
            executor.submit(
                build_opportunity,
                stock["ticker"],
                stock["sector"],
                FORECAST_HORIZON
            ): stock["ticker"]
            for stock in stocks
        }

        for future in as_completed(futures):
            ticker = futures[future]

            try:
                opportunity = future.result()

                if opportunity is not None:
                    results.append(opportunity.model_dump())
                else:
                    print(f"⚠️ No opportunity generated for {ticker}")

            except Exception as error:
                print(f"❌ Failed to generate {ticker}: {error}")

    if not results:
        print("❌ No opportunities generated.")
        return 0

    db = SessionLocal()

    try:
        save_opportunities(
            db=db,
            opportunities=results,
            forecast_horizon=FORECAST_HORIZON
        )
    finally:
        db.close()

    print(f"✅ {len(results)} opportunities saved.")
    return len(results)


if __name__ == "__main__":
    print("🚀 Starting opportunity generation...")
    generate()
