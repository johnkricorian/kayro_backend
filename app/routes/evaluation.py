from fastapi import APIRouter

from app.services.prediction_evaluator import evaluate_pending_predictions

router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"]
)


@router.post("/run")
def run_evaluation():
    return evaluate_pending_predictions()
