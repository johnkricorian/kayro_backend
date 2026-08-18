import httpx

from app.config.adanos import (
    ADANOS_API_KEY,
    ADANOS_BASE_URL,
)
from app.core.logger import create_logger

logger = create_logger(__name__)


class AdanosClient:

    def __init__(self):
        self.base_url = ADANOS_BASE_URL
        self.api_key = ADANOS_API_KEY

    def get(
        self,
        endpoint: str,
        params: dict | None = None,
    ):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

        logger.info(
            "Adanos GET %s",
            endpoint
        )

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                url,
                params=params or {},
                headers=headers,
            )

        response.raise_for_status()

        return response.json()


adanos_client = AdanosClient()
