import os
from pathlib import Path
from threading import Lock

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_NAME = "ProsusAI/finbert"
LOCAL_MODEL_PATH = Path(os.getenv("FINBERT_MODEL_PATH", "/app/models/finbert"))

labels = ["Positive", "Negative", "Neutral"]

_tokenizer = None
_model = None
_lock = Lock()


def get_model_source():
    if LOCAL_MODEL_PATH.exists():
        return str(LOCAL_MODEL_PATH)

    return MODEL_NAME


def load_finbert():
    global _tokenizer, _model

    if _tokenizer is None or _model is None:
        with _lock:
            if _tokenizer is None or _model is None:
                model_source = get_model_source()
                print(f"📦 Loading FinBERT from {model_source}")

                _tokenizer = AutoTokenizer.from_pretrained(model_source)
                _model = AutoModelForSequenceClassification.from_pretrained(model_source)
                _model.eval()

                print("✅ FinBERT loaded")

    return _tokenizer, _model


def finbert_score(text: str):
    if not text or text.strip() == "":
        return 0.0, "Neutral"

    tokenizer, model = load_finbert()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()

    score = float(probs[0] - probs[1])
    sentiment = labels[int(np.argmax(probs))]

    return score, sentiment
