import os

FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_BASE_URL = os.getenv(
    "FMP_BASE_URL",
    "https://financialmodelingprep.com/stable"
)

if not FMP_API_KEY:
    raise RuntimeError("FMP_API_KEY is not configured")
