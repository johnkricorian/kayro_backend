from functools import lru_cache
from pathlib import Path

from joblib import load
from xgboost import XGBClassifier
from app.core.logger import create_logger
from app.core.exceptions import ModelNotFoundError

logger = create_logger(__name__)

MODEL_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "models"
)


def available_models() -> list[int]:
    """
    Returns every available forecast horizon.
    Example:
    [4, 7, 15, 30]
    """

    models = []

    for file in MODEL_DIR.glob("xgboost_*d.joblib"):
        try:
            horizon = (
                file.stem
                .replace("xgboost_", "")
                .replace("d", "")
            )

            models.append(int(horizon))

        except ValueError:
            continue

    return sorted(models)


@lru_cache(maxsize=None)
def load_model(
    forecast_horizon: int
) -> XGBClassifier:
    """
    Loads one XGBoost model.

    The model is cached after the first load,
    so disk access happens only once.
    """

    model_path = (
        MODEL_DIR
        / f"xgboost_{forecast_horizon}d.joblib"
    )

    if not model_path.exists():

        available = ", ".join(
            map(str, available_models())
        )

        raise ModelNotFoundError(
            f"Model '{model_path.name}' not found.\n"
            f"Available models: {available}"
        )

    logger.info(
        f"📦 Loading model "
        f"{model_path.name}"
    )

    return load(model_path)


def warmup_models():
    """
    Loads every model into memory.

    Call this once when FastAPI starts.
    """

    models = available_models()

    if not models:
        raise RuntimeError(
            "No XGBoost models found in app/models"
        )

    for horizon in models:
        load_model(horizon)

    logger.info(
        f"\n✅ {len(models)} XGBoost model(s) loaded."
    )


def clear_cache():
    """
    Clears model cache.

    Useful during development.
    """

    load_model.cache_clear()
