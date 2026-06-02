"""Бизнес-логика фичи models: реестр моделей и inference."""

import asyncio

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import ModelNotFoundError
from src.features.models.inference import parse_text
from src.features.models.repository import model_repository
from src.features.models.schemas import (
    ModelListItem,
    ModelListResponse,
    ParsedEntity,
    ParseResponse,
)


class ModelService:
    """Сервис работы с обученными моделями и разбора текста."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_list(self, page: int, page_size: int) -> ModelListResponse:
        """Возвращает постраничный список моделей."""
        offset = (page - 1) * page_size
        records, total = await model_repository.get_list(self._session, offset, page_size)
        return ModelListResponse(
            items=[ModelListItem.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, model_id: int):
        """Возвращает модель по идентификатору."""
        return await model_repository.get_by_id(self._session, model_id)

    async def parse(self, model_id: int, text: str) -> ParseResponse:
        """Разбирает текст указанной моделью на поля по меткам."""
        model = await model_repository.get_by_id(self._session, model_id)
        if model is None:
            raise ModelNotFoundError(f'Модель {model_id} не найдена.')

        # Загрузка модели и инференс — блокирующие, уносим в отдельный поток.
        fields, entities = await asyncio.to_thread(
            parse_text, model.artifact_path, text, model.label_names
        )
        return ParseResponse(
            text=text,
            fields=fields,
            entities=[ParsedEntity(**ent) for ent in entities],
        )


def get_model_service(session: AsyncSession = Depends(get_session)) -> ModelService:
    """Dependency: создаёт сервис с сессией текущего запроса."""
    return ModelService(session)
