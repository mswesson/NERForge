# Feature: training

Обучает spaCy NER-модель на готовом JSONL-датасете.

**Вход:** JSONL (выход фичи dataset).  
**Выход:** zip-архив с обученной моделью (`model-best`).

Что делает:
- Принимает JSONL, валидирует и запускает обучение в фоновой asyncio-задаче
- Стримит прогресс через SSE
- Упаковывает лучшую модель в zip для скачивания

Структура `services/`:
- `training_service.py` — оркестратор: валидация, запуск задачи, статус
- `trainer_service.py` — SpacyTrainer: DocBin, конфиг, вызов `spacy train`
- `job_store.py` — in-memory хранилище текущей задачи

Эндпоинты: `POST /train/`, `GET /train/{id}`, `GET /train/{id}/stream`, `GET /train/{id}/model`
