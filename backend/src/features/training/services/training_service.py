"""Оркестрация обучения без БД и брокера: фоновая asyncio-задача + in-memory статус."""

import asyncio
import json

from loguru import logger

from src.core.exceptions import EmptyDatasetError
from src.core.storage import job_workdir
from src.features.training.services.job_store import TrainingJob, TrainingStatus, store
from src.features.training.services.trainer_service import Sample, SpacyTrainer

# Имя файла загруженного JSONL внутри рабочей папки задачи.
_INPUT_FILE = 'input.jsonl'


def _read_jsonl(content: bytes) -> tuple[list[str], list[Sample]]:
    """Читает JSONL-датасет: возвращает список уникальных меток и обучающие примеры.

    Каждая строка JSONL: {"text": "...", "entities": [[start, end, "LABEL"], ...]}.
    """
    samples: list[Sample] = []
    labels_seen: set[str] = set()

    for line in content.decode('utf-8').splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        text: str = obj['text']
        entities = [(int(e[0]), int(e[1]), str(e[2])) for e in obj['entities']]
        for _, _, label in entities:
            labels_seen.add(label)
        samples.append((text, entities))

    if not samples:
        raise EmptyDatasetError('JSONL не содержит ни одного примера.')

    return sorted(labels_seen), samples


async def create_and_start(
    content: bytes, base_model: str, epochs: int, dropout: float
) -> TrainingJob:
    """Валидирует JSONL, заводит задачу и запускает обучение в фоне."""
    label_names, _ = _read_jsonl(content)
    job = store.create(label_names, base_model, epochs, dropout)

    # Сохраняем JSONL в свежую рабочую папку (предыдущие артефакты уже очищены).
    (job_workdir(job.id) / _INPUT_FILE).write_bytes(content)

    task = asyncio.create_task(run_training_job(job.id))
    store.set_task(task)
    return job


def get_status(job_id: int) -> TrainingJob | None:
    """Возвращает состояние задачи обучения по идентификатору."""
    return store.get(job_id)


async def run_training_job(job_id: int) -> None:
    """Фоновый прогон: чтение JSONL → обучение spaCy → упаковка модели."""
    try:
        job = store.get(job_id)
        if job is None:
            return

        store.update(job_id, status=TrainingStatus.GENERATING.value, progress=10)
        content = (job_workdir(job_id) / _INPUT_FILE).read_bytes()
        _, samples = _read_jsonl(content)

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
