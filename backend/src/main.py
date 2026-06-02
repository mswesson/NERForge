"""Точка входа: сборка FastAPI приложения, FastStream брокера и декларация очередей."""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from src.core import logger  # noqa: F401 — применяет настройку loguru
from src.core.broker import broker
from src.core.config import settings
from src.core.exceptions import (
    DatasetNotFoundError,
    EmptyDatasetError,
    ModelNotFoundError,
    TrainingJobNotFoundError,
)
from src.features.datasets.router import router as datasets_router
from src.features.models.router import router as models_router
from src.use_cases.training import consumers  # noqa: F401 — регистрирует subscriber в брокере
from src.use_cases.training.queues import training_queue
from src.use_cases.training.router import router as training_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: запуск брокера и декларация очередей."""
    # Базовые папки для артефактов моделей и задач обучения.
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)

    await broker.start()
    await broker.declare_queue(training_queue)
    yield
    await broker.stop()


app = FastAPI(
    title=settings.SERVICE_NAME,
    description='Универсальный тренер NER-моделей для разбиения строк на поля.',
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)


@app.exception_handler(DatasetNotFoundError)
@app.exception_handler(ModelNotFoundError)
@app.exception_handler(TrainingJobNotFoundError)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Маппинг доменных «не найдено» в HTTP 404."""
    return JSONResponse(status_code=404, content={'detail': str(exc)})


@app.exception_handler(EmptyDatasetError)
async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
    """Маппинг ошибки пустого/некорректного датасета в HTTP 400."""
    return JSONResponse(status_code=400, content={'detail': str(exc)})


v1_router = APIRouter(prefix='/v1')
v1_router.include_router(datasets_router)
v1_router.include_router(training_router)
v1_router.include_router(models_router)

app.include_router(v1_router)
