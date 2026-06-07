"""Точка входа: сборка FastAPI приложения (без БД и брокера)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core import logger  # noqa: F401 — применяет настройку loguru
from src.core.config import settings
from src.core.exceptions import (
    BaseModelUnavailableError,
    EmptyDatasetError,
    ModelNotFoundError,
    TrainingJobNotFoundError,
)
from src.features.dataset.router import router as dataset_router
from src.features.inference.router import router as inference_router
from src.features.training.router import router as training_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: подготовка папок для артефактов."""
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)
    settings.uploaded_models_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.SERVICE_NAME,
    description='Универсальный тренер NER-моделей для разбиения строк на поля.',
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(ModelNotFoundError)
@app.exception_handler(TrainingJobNotFoundError)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Маппинг доменных «не найдено» в HTTP 404."""
    return JSONResponse(status_code=404, content={'detail': str(exc)})


@app.exception_handler(EmptyDatasetError)
async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
    """Маппинг ошибки пустого/некорректного датасета в HTTP 400."""
    return JSONResponse(status_code=400, content={'detail': str(exc)})


@app.exception_handler(BaseModelUnavailableError)
async def base_model_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Базовая модель не установлена — HTTP 409 с инструкцией."""
    return JSONResponse(status_code=409, content={'detail': str(exc)})


app.include_router(dataset_router)
app.include_router(training_router)
app.include_router(inference_router)
