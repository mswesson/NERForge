# AGENTS.md — машинная спецификация проекта NERForge

Документ для LLM-агента. Плотный, без воды. Цель: мгновенно понять суть, карту файлов и как безопасно редактировать.

## 1. Суть

Веб-инструмент обучения spaCy NER-моделей, которые разбивают неструктурированную строку на поля (бренд/форма/дозировка/… — метки берутся из колонок CSV, домен не зашит). Поток stateless, файловый, 3 шага: (1) генерация зашумлённого обучающего CSV из эталонного CSV; (2) обучение модели из этого CSV → скачиваемый zip; (3) парсинг текста загруженной моделью. **Нет БД, нет брокера.** Статус обучения — в памяти процесса. Обучение — фоновая asyncio-задача; `spacy train` запускается дочерним процессом. На диске хранится только ПОСЛЕДНИЙ результат (каждый новый запуск чистит предыдущий).

## 2. Стек / версии

- Backend: Python 3.14, FastAPI (`fastapi[standard]`), spaCy ≥3.7, pandas, sse-starlette, loguru, pydantic-settings. Линтер/форматтер Ruff (line-length=99, одинарные кавычки для строк; docstrings — `"""` после `ruff format`). Комментарии/докстринги на русском.
- Frontend: React 19 + TypeScript + Vite 6 + Tailwind v4 + lucide-react. Без роутера (вкладки в `App.tsx`). API-слой в `src/api/client.ts`.
- Запуск: корневой `docker-compose.yml` (backend+frontend) ИЛИ локально (uvicorn + `npm run dev`).

## 3. Карта репозитория

```
/README.md                    обзор для людей
/AGENTS.md                    этот файл
/docker-compose.yml           backend(:8000)+frontend(:3000); build-arg SPACY_MODELS
/backend
  Dockerfile                  python:3.14-slim; ARG SPACY_MODELS="ru_core_news_sm ru_core_news_md" (lg НЕ по умолчанию) качает модели
  requirements.txt            БЕЗ sqlalchemy/faststream/alembic (удалены)
  .env.example .vscode/launch.json .dockerignore compose.dev.yaml(app-only)
  /src
    main.py                   FastAPI, CORS, lifespan(создаёт папки), подключает 3 роутера; exception_handlers
    /core
      config.py               Settings(pydantic): SERVICE_*, DATA_DIR(./data), CORS_ORIGINS; env_prefix NERFORGE_; extra='ignore'; singleton `settings`
      storage.py              reset_jobs_dir(), job_workdir(id), reset_uploaded_models_dir()
      logger.py               loguru JSON (импортируется первым в main)
      exceptions.py           EmptyDatasetError(400), ModelNotFoundError(404), TrainingJobNotFoundError(404), DomainError
    /features/generation      ШАГ 1 (синхронно)
      router.py               POST /v1/generate (multipart file + Form params) -> StreamingResponse text/csv
      service.py              generation_service.generate(content, sample_size, noise_ratio, typo_ratio, remove_whitespaces, truncate_words, lowercase) -> bytes(CSV)
    /features/inference       ШАГ 3 (stateless)
      inference.py            _load_from_zip(zip_bytes) кэш ОДНОЙ модели по sha256; смена модели => reset_uploaded_models_dir(); parse_uploaded()->(entities,labels)
      service.py router.py    POST /v1/parse (multipart model=zip + Form text) -> {text,entities[],labels[]}
    /use_cases/training       ШАГ 2 (async, in-memory)
      augmentation.py         ЧИСТЫЕ функции. ORDER_COLUMN='__ORDER__'. generate_rows(records,variations_per_row,noise_ratio,typo_ratio,remove_whitespaces,truncate_words,shuffle_order)->list[dict] (шаг1: шум+перемешивание порядка, порядок пишется в __ORDER__). assemble_from_order(fields,order)->Sample (курсор, без find). build_training_samples(rows)->list[Sample] (шаг2: собирает СТРОГО по __ORDER__, БЕЗ шаффла/шума).
      trainer.py              SpacyTrainer(workdir,base_model,epochs,dropout): prepare()=DocBin train/dev .spacy + init config; train()=spacy train -> (zip_path, metrics). sm=>optimize efficiency(без векторов); md/lg=>accuracy + --initialize.vectors. SUPPORTED_BASE_MODELS.
      store.py                TrainingStatus(enum), TrainingJob(dataclass), TrainingStore(однослотовый, in-memory) + singleton `store`. create() чистит прошлое+отменяет прошлый task.
      service.py              _read_csv(); create_and_start()->job + asyncio.create_task(run_training_job); run_training_job() обновляет store, ловит CancelledError/Exception.
      router.py               POST /v1/train; GET /v1/train/{id}; GET /v1/train/{id}/stream (SSE); GET /v1/train/{id}/model (FileResponse zip)
      schemas.py              TrainingStartResponse, TrainingStatusResponse (from_attributes=True, валидируются из dataclass)
  /tests/test_augmentation.py инвариант корректности спанов
/frontend
  Dockerfile(.dockerignore)   node:20; build с ARG VITE_API_URL; CMD vite preview :3000
  package.json                name nerforge-frontend; scripts dev/build/preview/lint(tsc --noEmit)
  /src
    api/client.ts             ЕДИНСТВЕННЫЙ слой API. generateDataset/startTraining/openTrainingStream(EventSource)/modelDownloadUrl/parseText/saveBlob. База: import.meta.env.VITE_API_URL ?? http://localhost:8000/v1
    App.tsx                   3 вкладки constructor|training|testing; держит preset/cleanRecords/config(+localStorage nf_*)
    types.ts                  PresetSchema, EntityLabel, AugmentationConfig(sampleSize,noiseRatio,typoRatio,shuffleOrder,removeWhitespaces,truncateWords,lowercase)
    presets.ts                демо-схемы (pharma/addresses/financial)
    components/DatasetGenerator.tsx  ШАГ1 UI: загрузка CSV/демо, слайдеры/чекбоксы шума, кнопка генерации ВНИЗУ, контент над ней
    components/ModelTrainer.tsx      ШАГ2 UI: загрузка CSV, base_model sm/md/lg, epochs, dropout, SSE-прогресс/метрики, скачать zip; кнопка ВНИЗУ
    components/PredictionPlayground.tsx ШАГ3 UI: загрузка zip модели, textarea, подсветка сущностей; цвета меток из ответа labels[]
    vite-env.d.ts            /// <reference types="vite/client" />
```

УДАЛЕНО (не воскрешать без явной причины): `core/database.py`, `core/broker.py`, `core/base.py`, `alembic.ini`, `src/migrations/`, `features/datasets/`, `features/models/`, training `models.py(ORM)/repository.py/consumers.py/publishers.py/queues.py`. В `frontend/src/generatorUtils.ts` были моки — удалён.

## 4. Контракт API (всё под `/v1`)

- `POST /generate` multipart: `file`(CSV колонки=метки, без id) + Form `variations_per_row,noise_ratio,typo_ratio,remove_whitespaces,truncate_words,shuffle_order,lowercase` → `text/csv`: те же колонки значений + служебная `__ORDER__` (порядок меток строки). Строк = записи × variations_per_row. Перемешивание порядка и шум — ЗДЕСЬ.
- `POST /train` multipart: `file`(обучающий CSV) + Form `base_model∈{ru_core_news_sm|md|lg},epochs(1..100),dropout(0..0.9)` → `{id,status,label_names,base_model,created_at}`.
- `GET /train/{id}` → `{id,status,progress,label_names,base_model,metrics,error,created_at,updated_at}`; status∈pending|generating|training|succeeded|failed.
- `GET /train/{id}/stream` → SSE, event `status` (data=TrainingStatusResponse json), закрывается на терминальном статусе; event `error` если job не найден.
- `GET /train/{id}/model` → zip (только succeeded; иначе ModelNotFoundError 404).
- `GET /train/base-models` → `[{value,installed}]` (installed = `spacy.util.is_package`). Старт обучения на неустановленной модели → `BaseModelUnavailableError` (409). Фронт (`ModelTrainer`) фетчит этот список, помечает «не загружена», блокирует кнопку и показывает предупреждение.
- `POST /parse` multipart: `model`(zip) + Form `text` → `{text,entities:[{label,text,start,end}],labels:[...]}`.

## 5. Поток данных шаг1→шаг2

CSV шага1 = колонки значений (как на входе, с шумом) + служебная колонка `__ORDER__` (порядок меток для строки, через пробел). Один файл несёт и значения, и порядок. Аугментация (шум + перемешивание порядка) делается на ШАГЕ 1 и фиксируется в `__ORDER__`. Шаг 2 (`build_training_samples`) собирает строку СТРОГО по `__ORDER__`, ничего не перемешивая и не добавляя шум; спаны курсором. Если `__ORDER__` нет — фолбэк на порядок колонок. Метки = заголовки CSV в UPPERCASE, КРОМЕ `__ORDER__`. Объём шага1 = «вариаций на строку» (записи × N), а не общее число строк.

## 6. Инварианты / ловушки (НЕ ЛОМАТЬ)

- Спаны: `text[start:end]` всегда == значению; строятся курсором при сборке, НИКОГДА через `str.find` (иначе коллизии типа `10мг`/`10 шт`). Тест: `tests/test_augmentation.py`.
- Перемешивание порядка полей — ТОЛЬКО на шаге 1 (generate_rows). Шаг 2 детерминированный, использует датасет как есть. Не возвращать shuffle в обучение.
- spaCy: `--optimize accuracy` тянет слой статических векторов → для `sm` (нет векторов) это краш `IndexError ... size 0`. Поэтому sm⇒efficiency, md/lg⇒accuracy+`--initialize.vectors`. См. `trainer.py::_init_config` и `train`.
- spaCy `char_span(alignment_mode='contract')` может отбрасывать спаны не по границам токенов — нормально, влияет на метрики.
- Single-slot: `store.create()` вызывает `reset_jobs_dir()` (rmtree) и отменяет прошлый asyncio task; параллельных обучений нет.
- Статус в памяти ⇒ при рестарте процесса теряется (осознанно, БД убрана). API и фоновая задача — ОДИН процесс uvicorn; не разносить.
- VITE_API_URL зашивается на этапе сборки фронта (build-arg в Docker).
- CORS: origins из `settings.CORS_ORIGINS`; фронт по умолчанию :3000.
- Pydantic Settings `extra='ignore'` — старые env-переменные не валят старт.

## 7. Команды

Backend: `cd backend && ruff check src && ruff format src && python -m pytest tests/`. Запуск: `uvicorn src.main:app --reload --port 8000` (нужен venv + `python -m spacy download ru_core_news_sm`).
Frontend: `cd frontend && npm install && npm run lint && npm run build`; dev `npm run dev`.
Всё: из корня `docker compose up --build`. Облегчить образ: build-arg `SPACY_MODELS="ru_core_news_sm"`.

## 8. Как редактировать типовое

- Новый параметр шума: добавить в `AugmentationConfig`(types.ts) + чекбокс в DatasetGenerator + поле в client.GenerateConfig + Form в `generation/router.py` + аргумент в `generation/service.generate` + логику в `augmentation`. (См. как сделан `lowercase`.)
- Новый параметр обучения: Form в `training/router.start_training` → `service.create_and_start` → `store.TrainingJob`/`SpacyTrainer` → CLI-override в `trainer.train`.
- Новый эндпоинт: создать фичу-пакет (router/service/schemas) и подключить роутер в `main.py` под `v1_router`.
- Стиль: после правок прогнать `ruff format` (backend) и `tsc --noEmit` (frontend). Соблюдать существующий стиль; комментарии по-русски.
