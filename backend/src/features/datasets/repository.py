"""Репозиторий фичи datasets."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.datasets.models import Dataset, DatasetRecord


class DatasetRepository:
    """Доступ к данным таблиц datasets и dataset_records."""

    async def create(
        self,
        session: AsyncSession,
        name: str,
        label_names: list[str],
        records: list[tuple[str, dict[str, str]]],
    ) -> Dataset:
        """Создаёт датасет вместе с эталонными записями одним коммитом."""
        dataset = Dataset(
            name=name,
            label_names=label_names,
            records_count=len(records),
        )
        session.add(dataset)
        await session.flush()  # получаем dataset.id до вставки записей

        session.add_all(
            DatasetRecord(dataset_id=dataset.id, external_id=external_id, fields=fields)
            for external_id, fields in records
        )
        await session.commit()
        await session.refresh(dataset)
        return dataset

    async def get_by_id(self, session: AsyncSession, dataset_id: int) -> Dataset | None:
        """Возвращает датасет по идентификатору или None."""
        return await session.get(Dataset, dataset_id)

    async def get_list(
        self, session: AsyncSession, offset: int, limit: int
    ) -> tuple[list[Dataset], int]:
        """Возвращает постраничный список датасетов."""
        total = (await session.execute(select(func.count()).select_from(Dataset))).scalar_one()
        records = (
            (
                await session.execute(
                    select(Dataset).order_by(Dataset.created_at.desc()).offset(offset).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return list(records), total

    async def get_records(self, session: AsyncSession, dataset_id: int) -> list[DatasetRecord]:
        """Возвращает все эталонные записи датасета (для генерации обучающих данных)."""
        result = await session.execute(
            select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id)
        )
        return list(result.scalars().all())


dataset_repository = DatasetRepository()
