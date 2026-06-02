"""Бизнес-логика фичи datasets: парсинг CSV и сохранение датасета."""

import io

import pandas as pd
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.exceptions import EmptyDatasetError
from src.features.datasets.models import Dataset
from src.features.datasets.repository import dataset_repository
from src.features.datasets.schemas import (
    DatasetListItem,
    DatasetListResponse,
)


class DatasetService:
    """Сервис загрузки и чтения датасетов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upload(self, name: str, content: bytes) -> Dataset:
        """Парсит CSV и сохраняет датасет с эталонными записями.

        Первая колонка — внешний id товара, остальные — эталонные поля.
        Имена меток берутся из заголовков колонок (верхний регистр).
        """
        label_names, records = self._parse_csv(content)
        return await dataset_repository.create(self._session, name, label_names, records)

    @staticmethod
    def _parse_csv(content: bytes) -> tuple[list[str], list[tuple[str, dict[str, str]]]]:
        """Разбирает CSV в список меток и список записей (external_id, {LABEL: value})."""
        frame = pd.read_csv(io.BytesIO(content), dtype=str).fillna('')
        if frame.shape[1] < 2:
            raise EmptyDatasetError('CSV должен содержать колонку id и хотя бы одно поле-метку.')

        id_column = frame.columns[0]
        label_columns = list(frame.columns[1:])
        # Метки — имена колонок в верхнем регистре (как в spaCy).
        label_names = [str(column).upper() for column in label_columns]

        records: list[tuple[str, dict[str, str]]] = []
        for _, row in frame.iterrows():
            external_id = str(row[id_column]).strip()
            fields = {
                str(column).upper(): str(row[column]).strip()
                for column in label_columns
                if str(row[column]).strip()
            }
            # Запись без непустых полей бесполезна для обучения — пропускаем.
            if external_id and fields:
                records.append((external_id, fields))

        if not records:
            raise EmptyDatasetError('CSV не содержит ни одной валидной записи.')

        return label_names, records

    async def get_list(self, page: int, page_size: int) -> DatasetListResponse:
        """Возвращает постраничный список датасетов."""
        offset = (page - 1) * page_size
        records, total = await dataset_repository.get_list(self._session, offset, page_size)
        return DatasetListResponse(
            items=[DatasetListItem.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, dataset_id: int) -> Dataset | None:
        """Возвращает датасет по идентификатору."""
        return await dataset_repository.get_by_id(self._session, dataset_id)


def get_dataset_service(session: AsyncSession = Depends(get_session)) -> DatasetService:
    """Dependency: создаёт сервис с сессией текущего запроса."""
    return DatasetService(session)
