"""Модель таблицы training_jobs: задача обучения и её статус."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TrainingStatus(str, enum.Enum):
    """Статус задачи обучения."""

    PENDING = 'pending'
    GENERATING = 'generating'
    TRAINING = 'training'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class TrainingJob(Base):
    """Задача обучения модели на конкретном датасете."""

    __tablename__ = 'training_jobs'
    __table_args__ = {'comment': 'Задачи обучения NER-моделей.'}

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment='Идентификатор задачи.'
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey('datasets.id'), index=True, comment='Датасет для обучения.'
    )
    status: Mapped[str] = mapped_column(
        String(32), default=TrainingStatus.PENDING.value, comment='Статус задачи обучения.'
    )
    progress: Mapped[int] = mapped_column(
        Integer, default=0, comment='Прогресс обучения, проценты 0-100.'
    )
    samples_per_record: Mapped[int] = mapped_column(
        Integer, comment='Сколько вариантов генерировать на одну эталонную запись.'
    )
    metrics: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment='Метрики качества: {ents_f, ents_p, ents_r}.'
    )
    model_id: Mapped[int | None] = mapped_column(
        ForeignKey('models.id'), nullable=True, comment='Созданная модель (после успеха).'
    )
    error: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment='Текст ошибки при статусе failed.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True, comment='Дата и время создания.'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Дата и время последнего обновления.',
    )
