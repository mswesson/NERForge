"""HTTP API обучения: запуск, статус, SSE-поток и скачивание модели."""

import asyncio
import json

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from src.core.exceptions import (
    BaseModelUnavailableError,
    ModelNotFoundError,
    TrainingJobNotFoundError,
)
from src.use_cases.training import service
from src.use_cases.training.schemas import TrainingStartResponse, TrainingStatusResponse
from src.use_cases.training.store import TrainingStatus
from src.use_cases.training.trainer import (
    BASE_MODEL_ORDER,
    SUPPORTED_BASE_MODELS,
    installed_base_models,
)

router = APIRouter(prefix='/train', tags=['Обучение'])

# Терминальные статусы, на которых SSE-поток закрывается.
_TERMINAL = {TrainingStatus.SUCCEEDED.value, TrainingStatus.FAILED.value}


@router.get('/base-models')
async def list_base_models() -> list[dict]:
    """Список базовых моделей spaCy с флагом, установлена ли модель в окружении."""
    installed = installed_base_models()
    return [{'value': model, 'installed': model in installed} for model in BASE_MODEL_ORDER]


@router.post('/', response_model=TrainingStartResponse)
async def start_training(
    file: UploadFile = File(..., description='CSV с обучающими данными (колонки = метки)'),
    base_model: str = Form('ru_core_news_sm', description='Базовая модель spaCy'),
    epochs: int = Form(10, ge=1, le=100, description='Максимум эпох'),
    dropout: float = Form(0.2, ge=0.0, le=0.9, description='Коэффициент dropout'),
) -> TrainingStartResponse:
    """Принимает CSV и запускает обучение в фоне (предыдущий результат очищается)."""
    chosen_model = base_model if base_model in SUPPORTED_BASE_MODELS else 'ru_core_news_sm'
    if chosen_model not in installed_base_models():
        raise BaseModelUnavailableError(
            f'Базовая модель {chosen_model} не установлена. Скачайте её '
            f'(python -m spacy download {chosen_model}) или выберите другую.'
        )
    content = await file.read()
    job = await service.create_and_start(
        content=content, base_model=chosen_model, epochs=epochs, dropout=dropout
    )
    return TrainingStartResponse.model_validate(job)


@router.get('/{job_id}', response_model=TrainingStatusResponse)
async def get_training(job_id: int) -> TrainingStatusResponse:
    """Возвращает текущий статус задачи обучения."""
    job = service.get_status(job_id)
    if job is None:
        raise TrainingJobNotFoundError(f'Задача обучения {job_id} не найдена.')
    return TrainingStatusResponse.model_validate(job)


@router.get('/{job_id}/stream')
async def stream_training(job_id: int) -> EventSourceResponse:
    """SSE-поток статуса задачи: события до достижения терминального статуса."""

    async def event_generator():
        """Читает статус из памяти и шлёт события, пока задача не завершится."""
        while True:
            job = service.get_status(job_id)
            if job is None:
                yield {'event': 'error', 'data': json.dumps({'detail': 'job not found'})}
                break

            yield {
                'event': 'status',
                'data': TrainingStatusResponse.model_validate(job).model_dump_json(),
            }
            if job.status in _TERMINAL:
                break
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@router.get('/{job_id}/model')
async def download_model(job_id: int) -> FileResponse:
    """Отдаёт zip обученной модели (только при успешном завершении)."""
    job = service.get_status(job_id)
    if job is None:
        raise TrainingJobNotFoundError(f'Задача обучения {job_id} не найдена.')
    if job.status != TrainingStatus.SUCCEEDED.value or not job.model_zip_path:
        raise ModelNotFoundError(f'Модель для задачи {job_id} ещё не готова.')
    return FileResponse(
        job.model_zip_path,
        media_type='application/zip',
        filename=f'nerforge_model_{job_id}.zip',
    )
