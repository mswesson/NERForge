"""Генерация обучающего датасета и сборка обучающих примеров.

Разделение ответственности:
- Шаг 1 (generate_rows): из эталонных строк делает вариации — вносит шум в значения
  и фиксирует порядок полей в служебной колонке __ORDER__. Это и есть аугментация.
- Шаг 2 (build_training_samples): берёт готовые строки КАК ЕСТЬ — собирает текст в
  порядке из __ORDER__ и считает спаны курсором. Ничего не перемешивает и не шумит.

Ключевой инвариант: спаны считаются ПРИ сборке курсором (а не через find), поэтому
для любого примера text[start:end] == значение поля даже при совпадающих значениях.
"""

import random

# Тип одного обучающего примера: текст и список спанов (start, end, LABEL).
Sample = tuple[str, list[tuple[int, int, str]]]

# Служебная колонка в сгенерированном CSV: порядок меток в строке (через пробел).
ORDER_COLUMN = '__ORDER__'


def drop_spaces(value: str, rng: random.Random) -> str:
    """Убирает внутренние пробелы значения (имитация «25 мг» → «25мг»)."""
    if ' ' not in value:
        return value
    return value.replace(' ', '') if rng.random() < 0.7 else value


def make_typo(value: str, rng: random.Random) -> str:
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


def abbreviate(value: str, rng: random.Random) -> str:
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
    """Зашумляет одно значение согласно настройкам шага генерации."""
    noised = value
    if remove_whitespaces:
        noised = drop_spaces(noised, rng)
    if truncate_words:
        noised = abbreviate(noised, rng)
    if rng.random() < typo_ratio:
        candidate = make_typo(noised, rng)
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
    """Шаг 1: на каждую эталонную строку делает variations_per_row вариаций.

    Каждая вариация — это значения по тем же колонкам (с шумом) + колонка __ORDER__
    с порядком меток. Первая вариация каждой строки — чистая, в исходном порядке.
    """
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []

    for fields in records:
        if not fields:
            continue
        labels = list(fields.keys())
        for index in range(variations_per_row):
            # index == 0 — опорная чистая вариация в исходном порядке.
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
            row[ORDER_COLUMN] = ' '.join(order)
            rows.append(row)

    return rows


def assemble_from_order(fields: dict[str, str], order: list[str]) -> Sample:
    """Собирает текст из значений в заданном порядке и считает спаны курсором."""
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
    """Шаг 2: из готовых строк собирает обучающие примеры КАК ЕСТЬ (без шума/шаффла).

    Порядок берётся из колонки __ORDER__; если её нет — порядок колонок строки.
    """
    samples: list[Sample] = []
    for row in rows:
        order_raw = row.get(ORDER_COLUMN, '')
        order = [token.upper() for token in order_raw.split()] if order_raw else []
        fields = {key: value for key, value in row.items() if key != ORDER_COLUMN and value}
        if not fields:
            continue
        if not order:
            order = list(fields.keys())
        text, entities = assemble_from_order(fields, order)
        if entities:
            samples.append((text, entities))
    return samples
