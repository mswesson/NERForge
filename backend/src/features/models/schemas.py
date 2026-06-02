"""Pydantic схемы фичи models."""

from datetime import datetime

from pydantic import BaseModel


class ModelListItem(BaseModel):
    """Элемент списка для эндпоинта list_models."""

    id: int
    name: str
    dataset_id: int
    label_names: list[str]
    metrics: dict
    status: str
    created_at: datetime

    model_config = {'from_attributes': True}


class ModelListResponse(BaseModel):
    """Ответ эндпоинта GET /models — постраничный список."""

    items: list[ModelListItem]
    total: int
    page: int
    page_size: int


class ModelGetResponse(BaseModel):
    """Ответ эндпоинта GET /models/{id} — одна модель."""

    id: int
    name: str
    dataset_id: int
    label_names: list[str]
    metrics: dict
    status: str
    created_at: datetime

    model_config = {'from_attributes': True}


class ParseRequest(BaseModel):
    """Тело запроса POST /models/{id}/parse."""

    text: str


class ParsedEntity(BaseModel):
    """Одна распознанная сущность в тексте."""

    label: str
    text: str
    start: int
    end: int


class ParseResponse(BaseModel):
    """Ответ эндпоинта POST /models/{id}/parse — разбивка текста по полям."""

    text: str
    fields: dict[str, str | None]
    entities: list[ParsedEntity]
