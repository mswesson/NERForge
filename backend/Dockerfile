# Multi-stage сборка образа сервиса NERForge.

# --- base: общий слой с зависимостями ---
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости для сборки колёс (spacy и пр.).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- production: код приложения ---
FROM base AS production

COPY . .

# Папка для артефактов моделей и задач обучения (монтируется как volume).
RUN mkdir -p /app/data/models /app/data/jobs

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
