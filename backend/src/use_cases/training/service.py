"""Оркестрация обучения без БД и брокера: фоновая asyncio-задача + in-memory статус."""

import asyncio
import io

import pandas as pd
from loguru import logger

from src.core.exceptions import EmptyDatasetError
from src.core.storage import job_workdir
from src.use_cases.training.augmentation import ORDER_COLUMN, build_training_samples
from src.use_cases.training.store import TrainingJob, TrainingStatus, store
from src.use_cases.training.trainer import SpacyTrainer

# Имя файла загруженного обучающего CSV внутри рабочей папки задачи.
_INPUT_CSV = 'input.csv'


def _read_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Разбирает обучающий CSV в список меток и строки (ключи в верхнем регистре).

    Служебная колонка __ORDER__ исключается из меток, но сохраняется в строках.
    """
    frame = pd.read_csv(io.BytesIO(content), dtype=str).fillna('')
    if frame.shape[1] < 1:
        raise EmptyDatasetError('CSV не содержит колонок.')

    columns = [str(column).upper() for column in frame.columns]
    label_names = [column for column in columns if column != ORDER_COLUMN]
    if not label_names:
        raise EmptyDatasetError('CSV не содержит колонок-меток.')

    rows: list[dict[str, str]] = []
    for _, row in frame.iterrows():
        record = {
            str(column).upper(): str(value).strip() for column, value in row.items()
        }
        # Строка валидна, если есть хотя бы одно непустое поле-метка.
        if any(record.get(label) for label in label_names):
            rows.append(record)

    if not rows:
        raise EmptyDatasetError('CSV не содержит ни одной валидной строки.')

    return label_names, rows


async def create_and_start(
    content: bytes, base_model: str, epochs: int, dropout: float
) -> TrainingJob:
    """Валидирует CSV, заводит задачу и запускает обучение в фоне."""
    label_names, _ = _read_csv(content)  # валидация + извлечение меток
    job = store.create(label_names, base_model, epochs, dropout)

    # Сохраняем CSV в свежую рабочую папку (предыдущие артефакты уже очищены).
    (job_workdir(job.id) / _INPUT_CSV).write_bytes(content)

    task = asyncio.create_task(run_training_job(job.id))
    store.set_task(task)
    return job


def get_status(job_id: int) -> TrainingJob | None:
    """Возвращает состояние задачи обучения по идентификатору."""
    return store.get(job_id)


async def run_training_job(job_id: int) -> None:
    """Фоновый прогон: чтение CSV → сборка примеров → обучение spaCy → упаковка модели."""
    try:
        job = store.get(job_id)
        if job is None:
            return

        store.update(job_id, status=TrainingStatus.GENERATING.value, progress=10)
        content = (job_workdir(job_id) / _INPUT_CSV).read_bytes()
        _, rows = _read_csv(content)
        samples = await asyncio.to_thread(build_training_samples, rows)

        trainer = SpacyTrainer(
            job_workdir(job_id), base_model=job.base_model, epochs=job.epochs, dropout=job.dropout
        )
        await trainer.prepare(samples)
        store.update(job_id, status=TrainingStatus.TRAINING.value, progress=50)
        zip_path, metrics = await trainer.train()

        store.update(
            job_id,
            status=TrainingStatus.SUCCEEDED.value,
            progress=100,
            metrics=metrics,
            model_zip_path=str(zip_path),
        )
        logger.info('Обучение завершено', job_id=job_id, metrics=metrics)
    except asyncio.CancelledError:
        # Задачу отменили (начали новое обучение) — тихо выходим.
        raise
    except Exception as error:
        logger.exception('Обучение упало', job_id=job_id)
        store.update(job_id, status=TrainingStatus.FAILED.value, error=str(error))
