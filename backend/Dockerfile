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

# Базовые модели spaCy для русского. По умолчанию БЕЗ тяжёлой lg (~500 МБ).
# Изменить список можно build-аргументом, например добавить lg:
#   --build-arg SPACY_MODELS="ru_core_news_sm ru_core_news_md ru_core_news_lg"
# или оставить только лёгкую:  --build-arg SPACY_MODELS="ru_core_news_sm"
ARG SPACY_MODELS="ru_core_news_sm ru_core_news_md"
RUN for model in $SPACY_MODELS; do python -m spacy download "$model"; done

# --- production: код приложения ---
FROM base AS production

COPY . .

# Папки для рабочих директорий обучения и загруженных моделей (монтируются как volume).
RUN mkdir -p /app/data/jobs /app/data/uploaded_models

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
