"""Pydantic схемы фичи training."""

from datetime import datetime

from pydantic import BaseModel


class TrainingStartResponse(BaseModel):
    """Ответ эндпоинта POST /train — созданная задача."""

    id: int
    status: str
    label_names: list[str]
    base_model: str
    created_at: datetime

    model_config = {'from_attributes': True}


class TrainingStatusResponse(BaseModel):
    """Ответ эндпоинтов статуса/SSE — текущее состояние задачи."""

    id: int
    status: str
    progress: int
    label_names: list[str]
    base_model: str
    metrics: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
