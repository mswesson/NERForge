"""Pydantic схемы фичи datasets."""

from datetime import datetime

from pydantic import BaseModel


class DatasetUploadResponse(BaseModel):
    """Ответ эндпоинта POST /datasets — созданный датасет."""

    id: int
    name: str
    label_names: list[str]
    records_count: int
    created_at: datetime

    model_config = {'from_attributes': True}


class DatasetListItem(BaseModel):
    """Элемент списка для эндпоинта list_datasets."""

    id: int
    name: str
    label_names: list[str]
    records_count: int
    created_at: datetime

    model_config = {'from_attributes': True}


class DatasetListResponse(BaseModel):
    """Ответ эндпоинта GET /datasets — постраничный список."""

    items: list[DatasetListItem]
    total: int
    page: int
    page_size: int


class DatasetGetResponse(BaseModel):
    """Ответ эндпоинта GET /datasets/{id} — один датасет."""

    id: int
    name: str
    label_names: list[str]
    records_count: int
    created_at: datetime

    model_config = {'from_attributes': True}
