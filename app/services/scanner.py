import pandas as pd
import time

from app.services.scoring import build_stock_score
from app.services.sector_loader import get_sector_stocks
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services import sector_cache
from app.services.score_engine import build_stock_score
from app.core.logger import create_logger

logger = create_logger(__name__)

start = time.perf_counter()

def scan_sector(
    sector: str,
    limit: int = 20
) -> list[dict]:

    start = time.perf_counter()

    cached = sector_cache.get(sector)

    if cached is not None:
        logger.info(f"⚡ Sector cache hit {sector}")
        return cached[:limit]

    stocks = get_sector_stocks(sector)
    results = []

    max_workers = min(8, len(stocks))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                build_stock_score,
                stock["ticker"]
            ): stock["ticker"]
            for stock in stocks
        }

        completed = 0

        for future in as_completed(futures):
            ticker = futures[future]
            completed += 1

            try:
                score = future.result()

                if score is not None:
                    results.append(score)

            except Exception as error:
                logger.info(f"❌ {ticker}: {error}")

            logger.info("[%d/%d] %s", completed, len(stocks), ticker)

    results = sorted(
        results,
        key=lambda item: item["kayro_score"],
        reverse=True
    )

    sector_cache.set(
        sector=sector,
        value=results
    )

    elapsed = time.perf_counter() - start
    logger.info(f"\n⚡ scan_sector completed in {elapsed:.2f}s")

    return results[:limit]
