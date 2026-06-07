"""In-memory хранилище состояния обучения (без БД).

Храним только ОДНУ — последнюю — задачу обучения. Каждый новый запуск очищает
предыдущие артефакты на диске и заменяет текущую задачу в памяти.
"""

import asyncio
import enum
import itertools
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.core import storage


class TrainingStatus(str, enum.Enum):
    """Статус задачи обучения."""

    PENDING = 'pending'
    GENERATING = 'generating'
    TRAINING = 'training'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


@dataclass
class TrainingJob:
    """Состояние задачи обучения в памяти."""

    id: int
    status: str
    progress: int
    label_names: list[str]
    base_model: str
    epochs: int
    dropout: float
    metrics: dict | None = None
    model_zip_path: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class TrainingStore:
    """Однослотовое хранилище: только текущая задача обучения."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)
        self._current: TrainingJob | None = None
        self._task: asyncio.Task | None = None

    def create(
        self, label_names: list[str], base_model: str, epochs: int, dropout: float
    ) -> TrainingJob:
        """Очищает прошлые артефакты, отменяет прошлую задачу и заводит новую."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
        storage.reset_jobs_dir()

        job = TrainingJob(
            id=next(self._counter),
            status=TrainingStatus.PENDING.value,
            progress=0,
            label_names=label_names,
            base_model=base_model,
            epochs=epochs,
            dropout=dropout,
        )
        self._current = job
        return job

    def get(self, job_id: int) -> TrainingJob | None:
        """Возвращает задачу, если это текущая; иначе None."""
        if self._current is not None and self._current.id == job_id:
            return self._current
        return None

    def update(self, job_id: int, **fields) -> None:
        """Обновляет поля текущей задачи (обновления устаревшей задачи игнорируются)."""
        job = self.get(job_id)
        if job is None:
            return
        for key, value in fields.items():
            if value is not None:
                setattr(job, key, value)
        job.updated_at = datetime.now(UTC)

    def set_task(self, task: asyncio.Task) -> None:
        """Сохраняет ссылку на фоновую задачу, чтобы её не собрал GC."""
        self._task = task


store = TrainingStore()
