"""Модели таблиц фичи datasets: загруженный датасет и его эталонные записи."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Dataset(Base):
    """Загруженный пользователем датасет (один CSV-файл)."""

    __tablename__ = 'datasets'
    __table_args__ = {'comment': 'Загруженные датасеты с эталонными полями.'}

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment='Идентификатор датасета.'
    )
    name: Mapped[str] = mapped_column(String(256), comment='Имя датасета (имя файла).')
    label_names: Mapped[list[str]] = mapped_column(
        JSONB, comment='Список меток (имена колонок CSV в верхнем регистре).'
    )
    records_count: Mapped[int] = mapped_column(
        Integer, comment='Количество эталонных записей в датасете.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True, comment='Дата и время загрузки.'
    )


class DatasetRecord(Base):
    """Одна эталонная запись датасета: id товара и значения полей по меткам."""

    __tablename__ = 'dataset_records'
    __table_args__ = {'comment': 'Эталонные записи датасета (id + поля по меткам).'}

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment='Идентификатор записи.'
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey('datasets.id'), index=True, comment='Ссылка на датасет.'
    )
    external_id: Mapped[str] = mapped_column(
        String(256), comment='Внешний id товара (первая колонка CSV).'
    )
    fields: Mapped[dict[str, str]] = mapped_column(
        JSONB, comment='Значения полей по меткам: {LABEL: value}.'
    )
