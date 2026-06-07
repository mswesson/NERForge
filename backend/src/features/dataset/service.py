"""Генерация обучающего датасета из эталонного CSV.

Вход  — CSV, где колонки = метки (регистр не важен).
Выход — JSONL: каждая строка {"text": "...", "entities": [[start, end, "LABEL"], ...]}.

Весь цикл подготовки данных живёт здесь — training-фича получает уже готовые примеры
и не знает о внутреннем формате промежуточных строк.
"""

import io
import json
import random

import pandas as pd

from src.core.exceptions import EmptyDatasetError

# Тип обучающего примера: текст и список спанов (start, end, LABEL).
Sample = tuple[str, list[tuple[int, int, str]]]

# Служебная колонка: порядок меток в строке — внутренняя деталь, не экспортируется.
_ORDER_COLUMN = '__ORDER__'


def _drop_spaces(value: str, rng: random.Random) -> str:
    """Убирает внутренние пробелы значения (имитация «25 мг» → «25мг»)."""
    if ' ' not in value:
        return value
    return value.replace(' ', '') if rng.random() < 0.7 else value


def _make_typo(value: str, rng: random.Random) -> str:
    """Вносит мелкую опечатку: перестановка двух соседних символов или удаление одного."""
    if len(value) < 4:
        return value
    chars = list(value)
    index = rng.randrange(len(chars) - 1)
    if rng.random() < 0.5:
        chars[index], chars[index + 1] = chars[index + 1], chars[index]
    else:
        del chars[index]
    return ''.join(chars)


def _abbreviate(value: str, rng: random.Random) -> str:
    """Обрезает длинное слово до 3-4 букв (имитация «таблетки» → «таб»)."""
    words = value.split(' ')
    changed = False
    for i, word in enumerate(words):
        if len(word) > 5 and rng.random() < 0.5:
            words[i] = word[: rng.randint(3, 4)]
            changed = True
    return ' '.join(words) if changed else value


def _noise_value(
    value: str,
    rng: random.Random,
    *,
    typo_ratio: float,
    remove_whitespaces: bool,
    truncate_words: bool,
) -> str:
    """Зашумляет одно значение согласно настройкам генерации."""
    noised = value
    if remove_whitespaces:
        noised = _drop_spaces(noised, rng)
    if truncate_words:
        noised = _abbreviate(noised, rng)
    if rng.random() < typo_ratio:
        candidate = _make_typo(noised, rng)
        if candidate.strip():
            noised = candidate
    return noised if noised.strip() else value


def generate_rows(
    records: list[dict[str, str]],
    variations_per_row: int,
    *,
    noise_ratio: float,
    typo_ratio: float,
    remove_whitespaces: bool,
    truncate_words: bool,
    shuffle_order: bool,
    seed: int = 42,
) -> list[dict[str, str]]:
    """На каждую эталонную строку делает variations_per_row вариаций.

    Каждая вариация — значения с шумом + служебная колонка _ORDER_COLUMN с порядком меток.
    Первая вариация каждой строки — чистая, в исходном порядке.
    """
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []

    for fields in records:
        if not fields:
            continue
        labels = list(fields.keys())
        for index in range(variations_per_row):
            noised = index > 0 and rng.random() < noise_ratio
            if noised:
                values = {
                    label: _noise_value(
                        value,
                        rng,
                        typo_ratio=typo_ratio,
                        remove_whitespaces=remove_whitespaces,
                        truncate_words=truncate_words,
                    )
                    for label, value in fields.items()
                }
            else:
                values = dict(fields)

            order = list(labels)
            if shuffle_order and index > 0:
                rng.shuffle(order)

            row = dict(values)
            row[_ORDER_COLUMN] = ' '.join(order)
            rows.append(row)

    return rows


def _assemble_from_order(fields: dict[str, str], order: list[str]) -> Sample:
    """Собирает текст из значений в заданном порядке, считает спаны курсором.

    Спаны считаются при сборке, поэтому text[start:end] == значение поля
    даже при совпадающих значениях разных меток.
    """
    buffer: list[str] = []
    entities: list[tuple[int, int, str]] = []
    cursor = 0

    for label in order:
        value = fields.get(label, '')
        if not value:
            continue
        if buffer:
            buffer.append(' ')
            cursor += 1
        start = cursor
        buffer.append(value)
        cursor += len(value)
        entities.append((start, cursor, label))

    return ''.join(buffer), entities


def build_training_samples(rows: list[dict[str, str]]) -> list[Sample]:
    """Собирает обучающие примеры из строк с _ORDER_COLUMN.

    Порядок и метки берутся из _ORDER_COLUMN и приводятся к верхнему регистру.
    """
    samples: list[Sample] = []
    for row in rows:
        order_raw = row.get(_ORDER_COLUMN, '')
        order = [token.upper() for token in order_raw.split()] if order_raw else []
        fields = {
            key.upper(): value
            for key, value in row.items()
            if key != _ORDER_COLUMN and value
        }
        if not fields:
            continue
        if not order:
            order = list(fields.keys())
        text, entities = _assemble_from_order(fields, order)
        if entities:
            samples.append((text, entities))
    return samples


class GenerationService:
    """Сервис генерации датасета: аугментирует CSV и возвращает готовый JSONL."""

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
        """На каждую строку CSV генерирует variations_per_row обучающих примеров.

        Возвращает JSONL: каждая строка — {"text": "...", "entities": [[start, end, "LABEL"]]}.
        Метки в верхнем регистре; lowercase влияет только на текстовые значения.
        """
        frame = pd.read_csv(io.BytesIO(content), dtype=str).fillna('')
        if frame.shape[1] < 1:
            raise EmptyDatasetError('CSV не содержит колонок.')

        frame.columns = [str(c).upper() for c in frame.columns]
        columns = list(frame.columns)
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

        if lowercase:
            rows = [
                {
                    key: (value.lower() if key != _ORDER_COLUMN else value)
                    for key, value in row.items()
                }
                for row in rows
            ]

        samples = build_training_samples(rows)
        lines = [
            json.dumps(
                {'text': text, 'entities': [[s, e, label] for s, e, label in entities]},
                ensure_ascii=False,
            )
            for text, entities in samples
        ]
        return '\n'.join(lines).encode('utf-8')


generation_service = GenerationService()
