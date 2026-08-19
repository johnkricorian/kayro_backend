import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

FMP_BASE_URL = os.getenv(
    "FMP_BASE_URL",
    "https://financialmodelingprep.com"
)
