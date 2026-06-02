# NERForge — backend

Универсальный тренер NER-моделей для разбиения «грязных» строк на структурированные поля.

## Что делает

1. Принимает CSV: первая колонка — `id` товара, остальные — эталонные поля (бренд, форма, дозировка...).
2. Сам генерирует обучающий датасет: синтезирует «сырые» строки из полей + вносит шум
   (перемешивание порядка, удаление пробелов, опечатки, сокращения).
3. Обучает spaCy NER-модель в фоне (через RabbitMQ).
4. Сохраняет готовую модель и позволяет разбить произвольный текст на те же поля.

Метки берутся из заголовков колонок CSV — решение универсально, не привязано к домену.

## Стек

Python 3.14, FastAPI, FastStream (RabbitMQ), SQLAlchemy async + PostgreSQL, Alembic, spaCy, pandas.

## Локальный запуск

```bash
cp .env.example .env
docker compose -f compose.dev.yaml up --build
# применить миграции (внутри контейнера app):
docker compose -f compose.dev.yaml exec app alembic upgrade head
```

Swagger: http://localhost:8000/docs

## Поток работы (API)

1. `POST /v1/datasets` — загрузить CSV (multipart) → `dataset_id`, список меток.
2. `POST /v1/training` — `{dataset_id, samples_per_record}` → `job_id`, обучение уходит в очередь.
3. `GET /v1/training/{id}/stream` — SSE-поток статуса/прогресса до готовности модели.
4. `POST /v1/models/{id}/parse` — `{text}` → разбивка текста по полям.

## Структура

- `src/core/` — инфраструктура (конфиг, БД, брокер, логгер, хранилище артефактов).
- `src/features/datasets/` — загрузка и хранение датасетов.
- `src/features/models/` — реестр обученных моделей и inference (parse).
- `src/use_cases/training/` — генерация датасета, обучение, статус (SSE).
