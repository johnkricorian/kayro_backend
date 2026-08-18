import os

ADANOS_API_KEY = os.getenv("ADANOS_API_KEY")

ADANOS_BASE_URL = os.getenv(
    "ADANOS_BASE_URL",
    "https://api.adanos.org/reddit/stocks"
)

if not ADANOS_API_KEY:
    raise RuntimeError(
        "ADANOS_API_KEY is not configured"
    )
