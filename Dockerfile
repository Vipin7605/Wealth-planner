FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY frontend/dist ./frontend/dist
COPY ml ./ml
COPY data/ml_training_12m.csv ./data/ml_training_12m.csv
RUN python ml/train.py && useradd --create-home appuser && mkdir /app/runtime && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
