"""Бизнес-логика шага 1: генерация обучающего CSV из эталонного CSV.

Выход — один CSV: те же колонки (значения с шумом) + служебная колонка __ORDER__
с порядком меток для каждой строки. Так шаг 2 учится строго «как есть».
"""

import csv
import io

import pandas as pd

from src.core.exceptions import EmptyDatasetError
from src.use_cases.training.augmentation import ORDER_COLUMN, generate_rows


class GenerationService:
    """Сервис генерации обучающего датасета (синхронный, без БД)."""

    @staticmethod
    def generate(
        content: bytes,
        *,
        variations_per_row: int,
        noise_ratio: float,
        typo_ratio: float,
        remove_whitespaces: bool,
        truncate_words: bool,
        shuffle_order: bool,
        lowercase: bool = False,
    ) -> bytes:
        """На каждую строку входного CSV делает variations_per_row вариаций."""
        frame = pd.read_csv(io.BytesIO(content), dtype=str).fillna('')
        if frame.shape[1] < 1:
            raise EmptyDatasetError('CSV не содержит колонок.')

        columns = [str(column) for column in frame.columns]
        records = [
            {column: str(row[column]).strip() for column in columns}
            for _, row in frame.iterrows()
        ]
        records = [record for record in records if any(record.values())]
        if not records:
            raise EmptyDatasetError('CSV не содержит ни одной валидной строки.')

        rows = generate_rows(
            records,
            variations_per_row,
            noise_ratio=noise_ratio,
            typo_ratio=typo_ratio,
            remove_whitespaces=remove_whitespaces,
            truncate_words=truncate_words,
            shuffle_order=shuffle_order,
        )

        # Нижний регистр применяем только к значениям, не к служебной колонке порядка.
        if lowercase:
            rows = [
                {
                    key: (value.lower() if key != ORDER_COLUMN else value)
                    for key, value in row.items()
                }
                for row in rows
            ]

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=[*columns, ORDER_COLUMN])
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue().encode('utf-8')


generation_service = GenerationService()
