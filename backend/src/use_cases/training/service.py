"""Оркестрация обучения: HTTP-сервис и фоновый прогон задачи обучения.

HTTP-часть (TrainingService) работает на сессии запроса. Фоновый прогон
run_training_job открывает короткие собственные сессии на каждый шаг и не держит
соединение с БД открытым во время многоминутного обучения в дочернем процессе.
"""

import asyncio
import shutil

from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory, get_session
from src.core.exceptions import DatasetNotFoundError
from src.core.storage import job_workdir, model_dir
from src.features.datasets.repository import dataset_repository
from src.features.models.repository import model_repository
from src.use_cases.training.augmentation import generate_dataset
from src.use_cases.training.models import TrainingJob, TrainingStatus
from src.use_cases.training.publishers import publish_training_task
from src.use_cases.training.repository import training_repository
from src.use_cases.training.trainer import SpacyTrainer


class TrainingService:
    """HTTP-сервис управления задачами обучения."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(self, dataset_id: int, samples_per_record: int) -> TrainingJob:
        """Создаёт задачу обучения и публикует её в очередь."""
        dataset = await dataset_repository.get_by_id(self._session, dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(f'Датасет {dataset_id} не найден.')

        job = await training_repository.create(self._session, dataset_id, samples_per_record)
        await publish_training_task(job.id)
        return job

    async def get_status(self, job_id: int) -> TrainingJob | None:
        """Возвращает текущий статус задачи обучения."""
        return await training_repository.get_by_id(self._session, job_id)


def get_training_service(session: AsyncSession = Depends(get_session)) -> TrainingService:
    """Dependency: создаёт сервис с сессией текущего запроса."""
    return TrainingService(session)


async def _update(job_id: int, **fields) -> None:
    """Короткая сессия для обновления статуса/прогресса задачи."""
    async with async_session_factory() as session:
        await training_repository.update(session, job_id, **fields)


async def run_training_job(job_id: int) -> None:
    """Фоновый прогон: генерация датасета → обучение spaCy → регистрация модели."""
    # Читаем исходные данные короткой сессией и сразу её закрываем.
    async with async_session_factory() as session:
        job = await training_repository.get_by_id(session, job_id)
        if job is None:
            logger.warning('Задача обучения не найдена', job_id=job_id)
            return
        dataset = await training_repository.get_dataset(session, job.dataset_id)
        records = await training_repository.get_dataset_records(session, job.dataset_id)
        if dataset is None or not records:
            await training_repository.update(
                session,
                job_id,
                status=TrainingStatus.FAILED,
                error='Датасет пуст или не найден.',
            )
            return
        dataset_id = job.dataset_id
        dataset_name = dataset.name
        label_names = list(dataset.label_names)
        samples_per_record = job.samples_per_record
        fields_list = [record.fields for record in records]

    # Этап 1: генерация обучающей выборки с шумом.
    await _update(job_id, status=TrainingStatus.GENERATING, progress=10)
    samples = await asyncio.to_thread(generate_dataset, fields_list, samples_per_record)

    # Этап 2: подготовка .spacy + конфига и обучение.
    trainer = SpacyTrainer(job_workdir(job_id))
    await trainer.prepare(samples)
    await _update(job_id, status=TrainingStatus.TRAINING, progress=50)
    model_best, metrics = await trainer.train()

    # Этап 3: копируем артефакт в хранилище моделей и регистрируем модель.
    async with async_session_factory() as session:
        model = await model_repository.create(
            session,
            name=f'{dataset_name}-job{job_id}',
            dataset_id=dataset_id,
            label_names=label_names,
            artifact_path='',
            metrics=metrics,
        )
        destination = model_dir(model.id) / 'model-best'
        await asyncio.to_thread(shutil.copytree, model_best, destination, dirs_exist_ok=True)
        model.artifact_path = str(destination)
        await session.commit()
        model_id = model.id

    await _update(
        job_id,
        status=TrainingStatus.SUCCEEDED,
        progress=100,
        metrics=metrics,
        model_id=model_id,
    )
    logger.info('Обучение завершено', job_id=job_id, model_id=model_id, metrics=metrics)
