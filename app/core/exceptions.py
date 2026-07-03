class KayroError(Exception):
    status_code = 500
    message = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.message


class StockNotFoundError(KayroError):
    status_code = 404
    message = "Stock not found"


class ModelNotFoundError(KayroError):
    status_code = 500
    message = "Model not found"


class PortfolioError(KayroError):
    status_code = 400
    message = "Portfolio error"


class PredictionError(KayroError):
    status_code = 400
    message = "Prediction error"
