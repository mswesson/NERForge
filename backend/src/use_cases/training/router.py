"""HTTP API use_case training: запуск обучения, статус и SSE-поток."""

import asyncio
import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from src.core.database import async_session_factory
from src.core.exceptions import TrainingJobNotFoundError
from src.use_cases.training.models import TrainingStatus
from src.use_cases.training.repository import training_repository
from src.use_cases.training.schemas import (
    TrainingCreateRequest,
    TrainingCreateResponse,
    TrainingStatusResponse,
)
from src.use_cases.training.service import TrainingService, get_training_service

router = APIRouter(prefix='/training', tags=['Обучение'])

# Терминальные статусы, на которых SSE-поток закрывается.
_TERMINAL = {TrainingStatus.SUCCEEDED.value, TrainingStatus.FAILED.value}


@router.post('/', response_model=TrainingCreateResponse)
async def create_training(
    payload: TrainingCreateRequest,
    service: TrainingService = Depends(get_training_service),
) -> TrainingCreateResponse:
    """Создаёт задачу обучения и ставит её в очередь."""
    job = await service.create_job(
        dataset_id=payload.dataset_id,
        samples_per_record=payload.samples_per_record,
    )
    return TrainingCreateResponse.model_validate(job)


@router.get('/{job_id}', response_model=TrainingStatusResponse)
async def get_training(
    job_id: int,
    service: TrainingService = Depends(get_training_service),
) -> TrainingStatusResponse:
    """Возвращает текущий статус задачи обучения."""
    job = await service.get_status(job_id)
    if job is None:
        raise TrainingJobNotFoundError(f'Задача обучения {job_id} не найдена.')
    return TrainingStatusResponse.model_validate(job)


@router.get('/{job_id}/stream')
async def stream_training(job_id: int) -> EventSourceResponse:
    """SSE-поток статуса задачи: события до достижения терминального статуса."""

    async def event_generator():
        """Опрашивает БД свежей сессией и шлёт статус, пока задача не завершится."""
        while True:
            async with async_session_factory() as session:
                job = await training_repository.get_by_id(session, job_id)

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
