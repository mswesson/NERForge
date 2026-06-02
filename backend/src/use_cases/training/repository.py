"""Репозиторий use_case training: задачи обучения и чтение данных датасета."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.datasets.models import Dataset, DatasetRecord
from src.use_cases.training.models import TrainingJob, TrainingStatus


class TrainingRepository:
    """Доступ к таблице training_jobs и к данным датасета для обучения."""

    async def create(
        self, session: AsyncSession, dataset_id: int, samples_per_record: int
    ) -> TrainingJob:
        """Создаёт задачу обучения в статусе pending."""
        job = TrainingJob(
            dataset_id=dataset_id,
            samples_per_record=samples_per_record,
            status=TrainingStatus.PENDING.value,
            progress=0,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    async def get_by_id(self, session: AsyncSession, job_id: int) -> TrainingJob | None:
        """Возвращает задачу обучения по идентификатору."""
        return await session.get(TrainingJob, job_id)

    async def update(
        self,
        session: AsyncSession,
        job_id: int,
        *,
        status: TrainingStatus | None = None,
        progress: int | None = None,
        metrics: dict | None = None,
        model_id: int | None = None,
        error: str | None = None,
    ) -> None:
        """Обновляет поля задачи обучения и коммитит."""
        job = await session.get(TrainingJob, job_id)
        if job is None:
            return
        if status is not None:
            job.status = status.value
        if progress is not None:
            job.progress = progress
        if metrics is not None:
            job.metrics = metrics
        if model_id is not None:
            job.model_id = model_id
        if error is not None:
            job.error = error
        await session.commit()

    async def get_dataset(self, session: AsyncSession, dataset_id: int) -> Dataset | None:
        """Возвращает датасет (нужны имя и label_names для обучения)."""
        return await session.get(Dataset, dataset_id)

    async def get_dataset_records(
        self, session: AsyncSession, dataset_id: int
    ) -> list[DatasetRecord]:
        """Возвращает все эталонные записи датасета."""
        result = await session.execute(
            select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id)
        )
        return list(result.scalars().all())


training_repository = TrainingRepository()
