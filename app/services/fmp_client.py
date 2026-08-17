import httpx

from app.config.fmp import FMP_API_KEY, FMP_BASE_URL
from app.core.logger import create_logger

logger = create_logger(__name__)

class FMPClient:

    def __init__(self):
        self.base_url = FMP_BASE_URL
        self.api_key = FMP_API_KEY

    def get(
        self,
        endpoint: str,
        params: dict | None = None
    ):
        params = params or {}
        params["apikey"] = self.api_key

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.info(
            "FMP GET %s",
            endpoint
        )

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                url,
                params=params
            )

        response.raise_for_status()

        return response.json()


fmp_client = FMPClient()
