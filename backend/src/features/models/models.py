"""Модель таблицы models: реестр обученных NER-моделей."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Model(Base):
    """Обученная NER-модель: путь к артефакту на диске и метаданные."""

    __tablename__ = 'models'
    __table_args__ = {'comment': 'Реестр обученных NER-моделей.'}

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment='Идентификатор модели.'
    )
    name: Mapped[str] = mapped_column(String(256), comment='Имя модели.')
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey('datasets.id'), index=True, comment='Датасет, на котором обучена модель.'
    )
    label_names: Mapped[list[str]] = mapped_column(
        JSONB, comment='Список меток, которые распознаёт модель.'
    )
    artifact_path: Mapped[str] = mapped_column(
        String(512), comment='Путь к папке артефакта модели (model-best) на диске.'
    )
    metrics: Mapped[dict] = mapped_column(
        JSONB, comment='Метрики качества: {ents_f, ents_p, ents_r}.'
    )
    status: Mapped[str] = mapped_column(
        String(32), default='ready', comment='Статус модели (ready).'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True, comment='Дата и время создания.'
    )
