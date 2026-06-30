FROM python:3.11-slim

WORKDIR /app

ENV PORT=8080
ENV USE_TF=0
ENV TRANSFORMERS_NO_TF=1
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV FINBERT_MODEL_PATH=/app/models/finbert

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('ProsusAI/finbert').save_pretrained('/app/models/finbert'); AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert').save_pretrained('/app/models/finbert')"

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
