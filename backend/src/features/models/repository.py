"""Репозиторий фичи models."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.models.models import Model


class ModelRepository:
    """Доступ к данным таблицы models."""

    async def create(
        self,
        session: AsyncSession,
        name: str,
        dataset_id: int,
        label_names: list[str],
        artifact_path: str,
        metrics: dict,
    ) -> Model:
        """Создаёт запись об обученной модели и коммитит."""
        model = Model(
            name=name,
            dataset_id=dataset_id,
            label_names=label_names,
            artifact_path=artifact_path,
            metrics=metrics,
            status='ready',
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return model

    async def get_by_id(self, session: AsyncSession, model_id: int) -> Model | None:
        """Возвращает модель по идентификатору или None."""
        return await session.get(Model, model_id)

    async def get_list(
        self, session: AsyncSession, offset: int, limit: int
    ) -> tuple[list[Model], int]:
        """Возвращает постраничный список моделей."""
        total = (await session.execute(select(func.count()).select_from(Model))).scalar_one()
        records = (
            (
                await session.execute(
                    select(Model).order_by(Model.created_at.desc()).offset(offset).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return list(records), total


model_repository = ModelRepository()
