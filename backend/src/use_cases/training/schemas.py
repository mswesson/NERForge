"""Pydantic схемы use_case training."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrainingTaskMessage(BaseModel):
    """Сообщение в очередь RabbitMQ: запуск обучения по задаче."""

    job_id: int


class TrainingCreateRequest(BaseModel):
    """Тело запроса POST /training."""

    dataset_id: int
    samples_per_record: int = Field(10, ge=1, le=100, description='Вариантов на запись')


class TrainingCreateResponse(BaseModel):
    """Ответ эндпоинта POST /training — созданная задача."""

    id: int
    dataset_id: int
    status: str
    samples_per_record: int
    created_at: datetime

    model_config = {'from_attributes': True}


class TrainingStatusResponse(BaseModel):
    """Ответ эндпоинта GET /training/{id} — статус задачи."""

    id: int
    dataset_id: int
    status: str
    progress: int
    metrics: dict | None
    model_id: int | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
