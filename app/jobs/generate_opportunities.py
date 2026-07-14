from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

loaded = load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

from concurrent.futures import ThreadPoolExecutor, as_completed
from app.database.database import SessionLocal
from app.repositories.opportunity_repository import save_opportunities
from app.services.opportunity_service import build_opportunity
from app.services.sector_loader import load_sectors

FORECAST_HORIZON = 15
MAX_WORKERS = 2

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=False)

from app.database.database import SessionLocal
from app.repositories.opportunity_repository import (
    delete_stale_opportunities,
    upsert_opportunities,
)
from app.services.opportunity_service import build_opportunity
from app.services.sector_loader import load_sectors

FORECAST_HORIZON = 15
MAX_WORKERS = 2
BATCH_SIZE = 10


def save_batch(batch: list[dict]) -> int:
    if not batch:
        return 0

    db = SessionLocal()

    try:
        saved = upsert_opportunities(
            db=db,
            opportunities=batch,
            forecast_horizon=FORECAST_HORIZON,
        )

        print(f"💾 Batch saved: {saved} opportunities")
        return saved

    finally:
        db.close()

def generate() -> int:
    refresh_started_at = datetime.now(timezone.utc)

    sector_map = load_sectors()
    unique_stocks: dict[str, dict] = {}

    for sector, sector_stocks in sector_map.items():
        for stock in sector_stocks:
            ticker = stock["ticker"].upper()

            if ticker not in unique_stocks:
                unique_stocks[ticker] = {
                    "ticker": ticker,
                    "sector": sector.strip().lower(),
                }

    stocks = list(unique_stocks.values())

    print(
        f"🚀 Generating opportunities for "
        f"{len(stocks)} stocks..."
    )

    pending_batch: list[dict] = []
    saved_count = 0

    with ThreadPoolExecutor(
        max_workers=min(MAX_WORKERS, len(stocks))
    ) as executor:
        futures = {
            executor.submit(
                build_opportunity,
                stock["ticker"],
                stock["sector"],
                FORECAST_HORIZON,
            ): stock["ticker"]
            for stock in stocks
        }

        for future in as_completed(futures):
            ticker = futures[future]

            try:
                opportunity = future.result()

                if opportunity is None:
                    print(
                        f"⚠️ No opportunity generated for {ticker}"
                    )
                    continue

                pending_batch.append(
                    opportunity.model_dump()
                )

                print(
                    f"✅ Opportunity generated for {ticker}"
                )

                if len(pending_batch) >= BATCH_SIZE:
                    saved_count += save_batch(pending_batch)
                    pending_batch.clear()

            except Exception as error:
                print(
                    f"❌ Failed to generate {ticker}: {error}"
                )

    if pending_batch:
        saved_count += save_batch(pending_batch)

    if saved_count == 0:
        print("❌ No opportunities generated.")
        return 0

    db = SessionLocal()

    try:
        deleted_count = delete_stale_opportunities(
            db=db,
            forecast_horizon=FORECAST_HORIZON,
            refresh_started_at=refresh_started_at,
        )
    finally:
        db.close()

    print(
        f"✅ Refresh completed: "
        f"{saved_count} saved, "
        f"{deleted_count} stale rows deleted."
    )

    return saved_count

if __name__ == "__main__":
    print("🚀 Starting opportunity generation...")
    generate()
