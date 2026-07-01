import pandas as pd
import time

from app.services.scoring import build_stock_score
from app.services.sector_loader import get_sector_stocks
from concurrent.futures import ThreadPoolExecutor, as_completed

start = time.perf_counter()

def scan_sector(
    sector: str,
    limit: int = 20
) -> list[dict]:

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
                print(f"❌ {ticker}: {error}")

            print(
                f"[{completed}/{len(stocks)}] {ticker}",
                end="\r",
                flush=True
            )

    results.sort(
        key=lambda stock: stock["final_score"],
        reverse=True
    )
    elapsed = time.perf_counter() - start
    print(f"\n⚡ scan_sector completed in {elapsed:.2f}s")
    return results[:limit]
